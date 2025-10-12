#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: db_manager.py
# @Time: 12/10/2025 10:51
# @Author: Amundsen Severus Rubeus Bjaaland
"""整个项目的数据库管理器."""


import threading
from functools import reduce
from pathlib import Path

import jieba  # type: ignore[reportMissingTypeStubs]
from sqlalchemy import Engine, create_engine, func
from sqlalchemy.orm import Session, scoped_session, sessionmaker

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


DB_FOLDER = DATA_DIR / "db"

if not DB_FOLDER.exists():
    DB_FOLDER.mkdir(parents=True, exist_ok=True)


def synchronized(func):
    func.__lock__ = threading.Lock()

    def lock_func(*args, **kwargs):
        with func.__lock__:
            return func(*args, **kwargs)

    return lock_func


class DBManager:
    """数据库管理器."""

    instance = None

    @synchronized
    def __new__(cls):
        if not cls.instance:
            cls.instance = super(DBManager, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        """初始化数据库管理器."""
        self.__counter: int = 0
        self.__db_dict: dict[
            Path, tuple[Engine, scoped_session[Session]],
        ] = {}

        while True:
            self.__connect(self.__counter)
            if self.__is_full(self.__counter):
                self.__counter += 1
            else:
                break

        self.__not_full: Path = self.__get_file_path(self.__counter)

    def __get_file_path(self, index: int) -> Path:
        db_file_name = f"novel_dl_{str(index).rjust(5, '0')}.sqlite"
        return DB_FOLDER / db_file_name

    def __connect(self, index: int) -> None:
        db_path = self.__get_file_path(index)
        engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(engine)
        session_factory = scoped_session(sessionmaker(bind=engine))
        self.__db_dict[db_path] = (engine, session_factory)

    def __is_full(self, index: int) -> bool:
        db_path = self.__get_file_path(index)
        if db_path not in self.__db_dict:
            self.__connect(index)
        _, session_factory = self.__db_dict[db_path]
        with session_factory() as session:
            total = session.query(func.count(BookTable.book_hash)).scalar()
        return total >= 5000

    def add_book(self, book: Book | BookItem) -> None:
        if isinstance(book, BookItem): book = item_to_book(book)
        for _, session_factory in self.__db_dict.values():
            with session_factory() as session:
                old_record = session.get(BookTable, hash_(book))
                if old_record is not None:
                    session.query(ChapterTable).filter(
                        ChapterTable.book_hash == hash_(book),
                    ).delete()
                    session.merge(book_to_record(book + record_to_book(old_record)))
                    session.commit()
                    return
        with self.__db_dict[self.__not_full][1]() as session:
            for i in set(jieba.cut_for_search(book.title)):  # type: ignore[reportUnknownVariableType]
                if not isinstance(i, str) or len(i) == 0: continue
                session.add(
                    IndexTable(
                        hash_=hash_(f"{hash_(book)}-{i}"),
                        word=i, book_hash=hash_(book),
                    ),
                )
            session.add(book_to_record(book))
            session.commit()
        if self.__is_full(self.__counter):
            self.__counter += 1
            self.__not_full = self.__get_file_path(self.__counter)
            self.__connect(self.__counter)

    def add_chapter(self, chapter: Chapter | ChapterItem) -> bool:
        if isinstance(chapter, ChapterItem): chapter = item_to_chapter(chapter)
        for _, session_factory in self.__db_dict.values():
            with session_factory() as session:
                book_record = session.get(BookTable, chapter.book_hash)
                if book_record is None: continue
                old_record = session.get(ChapterTable, hash_(chapter))
                if old_record is not None:
                    session.merge(chapter_to_record(chapter + record_to_chapter(old_record)))
                else:
                    session.add(chapter_to_record(chapter))
                session.commit()
                return True
        return False

    def search_book_by_hash(self, book_hash: str) -> Book | None:
        for _, session_factory in self.__db_dict.values():
            with session_factory() as session:
                record = session.get(BookTable, book_hash)
                if record is not None: return record_to_book(record)
        return None

    def search_book_by_name(self, name: str) -> list[Book]:
        words: list[str] = []
        for i in set(jieba.cut_for_search(name)):  # type: ignore[reportUnknownVariableType]
            if isinstance(i, str) and len(i) > 0:
                words.append(i)
        result: list[Book] = []
        for _, session_factory in self.__db_dict.values():
            with session_factory() as session:
                buffer = []
                for word in words:
                    hash_list = session.query(IndexTable.book_hash).filter(
                        IndexTable.word == word,
                    ).all()
                    buffer.append(set(i[0] for i in hash_list))
                buffer = reduce(lambda x, y: x & y, buffer)
                for i in buffer:
                    book = session.query(BookTable).filter(
                        BookTable.book_hash == i,
                    ).scalar()
                    result.append(record_to_book(book))
        return result
