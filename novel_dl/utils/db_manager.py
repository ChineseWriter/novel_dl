#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: db_manager.py
# @Time: 12/10/2025 10:51
# @Author: Amundsen Severus Rubeus Bjaaland
"""整个项目的数据库管理器."""


# 导入标准库
import threading
from functools import reduce
from pathlib import Path

# 导入第三方库
from sqlalchemy import Engine, create_engine, func
from sqlalchemy.orm import Session, scoped_session, sessionmaker

# 导入自定义库
from novel_dl.entity.base import Book, Chapter
from novel_dl.entity.convert import (
    book_to_record,
    chapter_to_record,
    item_to_book,
    item_to_chapter,
    record_to_book,
    record_to_chapter,
)
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.entity.models import Base, BookTable, ChapterTable, IndexTable
from novel_dl.settings import DATA_DIR
from novel_dl.utils.identify import hash_


# 设置数据库文件夹
DB_FOLDER = DATA_DIR / "db"
# 确保数据库文件夹存在
if not DB_FOLDER.exists():
    DB_FOLDER.mkdir(parents=True, exist_ok=True)


def synchronized(func):
    """单例模式装饰器."""
    func.__lock__ = threading.Lock()

    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func


def _get_file_path(index: int) -> Path:
    """根据索引获取数据库文件路径."""
    db_file_name = f"novel_dl_{str(index).rjust(5, '0')}.sqlite"
    return DB_FOLDER / db_file_name


def _merge_book(book: Book, old_book: Book, session: Session) -> None:
    """合并新旧书籍信息."""
    new_book = book + old_book
    # 提前删除合并后 hash 有变化但 index 没变化的章节
    # 防止出现存在的章节重复插入导致唯一约束检查失败的问题
    for i in old_book.chapters:
        for ii in new_book.chapters:
            if (i.index == ii.index) and (hash_(i) != hash_(ii)):
                session.query(ChapterTable).filter(
                    ChapterTable.book_hash == i.book_hash,
                ).delete()
    # 转换为数据库记录
    new_book = book_to_record(new_book)
    # 合并更新书籍记录
    session.merge(new_book)
    # 提交更改
    session.commit()


class DBManager:
    """数据库管理器."""

    instance = None

    @synchronized
    def __new__(cls) -> "DBManager":
        """实现单例模式."""
        if not cls.instance:
            cls.instance = super(DBManager, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        """初始化数据库管理器."""
        # 计数器, 用于生成数据库文件名以及标记使用了多少个数据库文件
        self.__counter: int = 0
        # 所有数据库连接的字典
        self.__db_dict: dict[
            Path, tuple[Engine, scoped_session[Session]],
        ] = {}
        # 连接数据库并确保至少有一个未满的数据库
        while True:
            self.__connect(self.__counter)
            if self.__is_full(self.__counter): self.__counter += 1
            else: break
        # 记录当前未满的数据库文件路径
        self.__not_full: Path = _get_file_path(self.__counter)

    def __connect(self, index: int) -> None:
        # 获取数据库文件路径
        db_path = _get_file_path(index)
        # 创建数据库连接、数据库表和会话工厂
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(engine)
        session_factory = scoped_session(sessionmaker(bind=engine))
        # 将连接和会话工厂存入字典
        self.__db_dict[db_path] = (engine, session_factory)

    def __is_full(self, index: int) -> bool:
        # 获取数据库文件路径
        db_path = _get_file_path(index)
        # 如果数据库未连接, 则先连接
        if db_path not in self.__db_dict:
            self.__connect(index)
        # 获取会话工厂并查询书籍数量
        _, session_factory = self.__db_dict[db_path]
        with session_factory() as session:
            total = session.query(func.count(BookTable.book_hash)).scalar()
        # 判断书籍数量是否达到上限(5000本)
        return total >= 5000

    def add_book(self, book: Book | BookItem) -> None:
        """添加书籍到数据库."""
        # 如果传入的是 BookItem, 则转换为 Book 对象
        if isinstance(book, BookItem): book = item_to_book(book)
        # 在每个数据库中执行
        for _, session_factory in self.__db_dict.values():
            # 创建会话
            with session_factory() as session:
                # 检查书籍是否已存在
                old_record = session.get(BookTable, hash_(book))
                # 如果书籍已存在, 则更新书籍信息并删除旧章节
                if old_record is not None:
                    # 合并新旧书籍信息
                    _merge_book(book, record_to_book(old_record), session)
                    return
        # 如果每个数据库都没有该书籍, 则添加到当前未满的数据库
        with self.__db_dict[self.__not_full][1]() as session:
            for i in set(book.title):
                # 添加索引记录
                session.add(IndexTable(
                    hash_     = hash_(f"{hash_(book)}-{i}"),
                    word      = i,
                    book_hash = hash_(book),
                ))
            # 添加书籍记录并提交更改
            book_record = book_to_record(book)
            session.add(book_record)
            session.commit()
        # 如果当前未满的数据库已满, 则更新计数器和未满数据库路径
        if self.__is_full(self.__counter):
            self.__counter += 1
            self.__not_full = self.__get_file_path(self.__counter)
            self.__connect(self.__counter)

    def add_chapter(self, chapter: Chapter | ChapterItem) -> bool:
        """添加章节到数据库."""
        # 如果传入的是 ChapterItem, 则转换为 Chapter 对象
        if isinstance(chapter, ChapterItem): chapter = item_to_chapter(chapter)
        # 在每个数据库中执行
        for _, session_factory in self.__db_dict.values():
            # 创建会话
            with session_factory() as session:
                # 检查章节所属的书籍是否存在
                book_record = session.get(BookTable, chapter.book_hash)
                # 如果书籍不存在, 则跳过该数据库
                if book_record is None: continue
                # 检查章节是否已存在
                old_record = session.get(ChapterTable, hash_(chapter))
                # 如果章节已存在, 则合并章节内容
                if old_record is not None:
                    new_chapter = chapter + record_to_chapter(old_record)
                    new_chapter = chapter_to_record(new_chapter)
                    session.merge(new_chapter)
                # 如果章节不存在, 则添加新章节
                else:
                    chapter_record = chapter_to_record(chapter)
                    session.add(chapter_record)
                # 提交更改并返回成功
                session.commit()
                return True
        # 如果每个数据库都没有该章节所属的书籍, 则返回失败
        return False

    def search_book_by_hash(self, book_hash: str) -> Book | None:
        """通过书籍哈希值搜索书籍."""
        # 在每个数据库中执行
        for _, session_factory in self.__db_dict.values():
            # 创建会话
            with session_factory() as session:
                # 查询书籍记录
                record = session.get(BookTable, book_hash)
                # 如果找到书籍记录, 则转换为 Book 对象并返回
                if record is not None: return record_to_book(record)
        # 如果每个数据库都没有该书籍, 则返回 None
        return None

    def search_book_by_name(self, name: str) -> list[Book]:
        """通过书名搜索书籍."""
        # 获取书名的分词结果
        words = set(name)
        # 初始化结果列表
        result: list[Book] = []
        # 在每个数据库中执行
        for _, session_factory in self.__db_dict.values():
            # 创建会话
            with session_factory() as session:
                # 初始化缓冲区
                book_hash_set_list: list[set[str]] = []
                # 遍历每个分词结果
                for word in words:
                    # 查询包含该分词的书籍哈希值列表
                    hash_list = session.query(IndexTable.book_hash).filter(
                        IndexTable.word == word,
                    ).all()
                    # 将哈希值集合添加到缓冲区
                    book_hash_set_list.append({i[0] for i in hash_list})
                # 求所有分词的哈希值集合的交集
                book_hash_set: set[str] = reduce(
                    lambda x, y: x & y, book_hash_set_list,
                )
                # 查询并转换为书籍记录, 添加到结果列表
                for i in book_hash_set:
                    # 查询书籍记录
                    book = session.query(BookTable).filter(
                        BookTable.book_hash == i,
                    ).scalar()
                    # 将书籍记录转换为 Book 对象并添加到结果列表
                    result.append(record_to_book(book))
        # 返回结果列表
        return result
