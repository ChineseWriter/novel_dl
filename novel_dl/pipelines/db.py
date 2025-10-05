#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: db.py
# @Time: 03/08/2025 10:21
# @Author: Amundsen Severus Rubeus Bjaaland
"""
# DBPipeline
该管道用于将经过检查的 BookItem 和 ChapterItem 保存到数据库中,
确保数据持久化存储和后续查询.
"""


# 导入标准库
from collections import defaultdict
# 导入第三方库: SQLAlchemy 的数据库管理方法
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
# 导入自定义库: 数据库基础类
from novel_dl.entity.models import Base
# 导入自定义库: 用于类型标注
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.entity.models import BookTable, ChapterTable, ContentTable
# 导入自定义库: 用于类型转换
from novel_dl.utils.convert import item_to_book, item_to_chapter
from novel_dl.utils.convert import book_to_record, chapter_to_record
from novel_dl.utils.convert import record_to_book, record_to_chapter


class DBPipeline:
    """
    # DBPipeline
    该管道用于将经过检查的 BookItem 和 ChapterItem 保存到数据库中,
    确保数据持久化存储和后续查询.
    
    ## 主要功能
    - 将 BookItem 和 ChapterItem 转换为对应的数据库模型对象.
    - 处理重复数据, 合并已有记录.
    - 提交事务, 确保数据持久化.
    
    ## 方法
    - open_spider(spider): 在爬虫启动时初始化数据库连接和会话.
    - close_spider(spider): 在爬虫关闭时释放数据库连接.
    - process_item(item, spider): 主入口, 根据 item 类型分发到对应保存方法.
    - save_book(book_item): 将 BookItem 保存到数据库, 处理重复记录.
    - save_chapter(chapter_item): 将 ChapterItem 保存到数据库, 处理重复记录.
    """
    
    def __init__(self):
        self.chapter_cache: dict[str, list[ChapterItem]] = defaultdict(list)
    
    # noinspection PyMethodMayBeStatic
    def open_spider(self, spider):
        # 获取数据库地址, 应为 URI 形式
        self.__db_uri = spider.crawler.settings.get(
            "DB_URI", "sqlite:///data/novel_dl.db"
        )
        # 初始化数据库引擎和会话
        self.__engine = create_engine(
            self.__db_uri, connect_args={'check_same_thread': False}
        )
        self.__session = scoped_session(sessionmaker(self.__engine))
        # 创建所有表
        Base.metadata.create_all(self.__engine)
    
    def close_spider(self, _):
        # 关闭数据库连接
        self.__engine.dispose()
    
    def process_item(self, item, spider):
        """
        # process_item
        对传入的 item 进行类型检查和保存.
        根据 item 的类型(BookItem 或 ChapterItem),
        分别调用对应的保存方法(save_book 或 save_chapter).
        若 item 类型不属于上述两者, 则不做任何处理.
        """
        # 判断 Item 的类型, 并依据类型进行处理
        if isinstance(item, BookItem):    self.save_book(item, spider)
        if isinstance(item, ChapterItem): self.save_chapter(item, spider)
        # 返回处理后的 item, 以便后续管道使用
        return item
    
    def save_book(self, book_item: BookItem, spider):
        """
        # save_book
        将 BookItem 保存到数据库.
        若数据库中已存在相同哈希值的记录, 则进行合并处理.
        """
        # 创建一个事务
        with self.__session() as session:
            # 将 Item 转换为 Book 对象
            book_obj = item_to_book(book_item)
            # 检查数据库中是否已有该书记录
            old_record = session.get(BookTable, book_obj.hash)
            # 若无则添加, 有则合并后更新
            if old_record is None:
                # 将 Book 对象转换为数据库记录
                book_record = book_to_record(book_obj)
                # 将记录加入数据库
                session.add(book_record)
            else:
                # 依据已有记录创建 Book 对象
                old_book_obj = record_to_book(old_record)
                # 合并两个 Book 对象
                new_book_obj = old_book_obj + book_obj
                # 将合并后的 Book 对象转换为数据库记录
                new_record = book_to_record(new_book_obj)
                # 更新数据库中的记录
                session.merge(new_record)
            spider.logger.debug(f"已保存书籍: {repr(book_item)}")
            # 提交事务, 保存更改
            session.commit()
        # 确认是否有 ChapterItem 先于 BookItem 到达
        if book_obj.hash in self.chapter_cache:
            spider.logger.debug("书籍记录到达, 将缓存的 ChapterItem 加入书籍记录中.")
            # 重新处理缓存的 ChapterItem
            for i in self.chapter_cache[book_obj.hash]:
                self.process_item(i, spider)
            # 删除该书籍下缓存的 ChapterItem
            self.chapter_cache.pop(book_obj.hash)
    
    def save_chapter(self, chapter_item: ChapterItem, spider):
        """
        # save_chapter
        将 ChapterItem 保存到数据库.
        若数据库中已存在相同哈希值的记录, 则进行合并处理.
        该方法会确保对应的 Book 记录已存在, 否则抛出异常.
        """
        # 创建一个事务
        with self.__session() as session:
            # 将 Item 转换为 Chapter 对象
            chapter_obj = item_to_chapter(chapter_item)
            # 确保对应的 Book 记录已存在
            book_hash = chapter_obj.book_hash
            book_record = session.get(BookTable, book_hash)
            # 如果对应的 Book 记录不存在, 则先缓存
            if book_record is None:
                spider.logger.debug(
                    f"书籍的 ChapterItem({repr(chapter_item)}) "
                    "先于 BookItem 到达."
                )
                self.chapter_cache[book_hash].append(chapter_item)
                return None
            # 检查数据库中是否已有该章节记录
            old_chapter_record = session.get(ChapterTable, chapter_obj.hash)
            old_content_record = session.get(ContentTable, chapter_obj.hash)
            # 若无则添加, 有则合并后更新
            if (old_chapter_record is None) or (old_content_record is None):
                # 将 Chapter 对象转换为数据库记录并加入数据库
                chapter_record = chapter_to_record(chapter_obj)
                session.add(chapter_record)
            else:
                # 依据已有记录创建 Chapter 对象
                old_chapter_obj = record_to_chapter(
                    old_chapter_record, old_content_record
                )
                # 合并两个 Chapter 对象
                new_chapter_obj = old_chapter_obj + chapter_obj
                # 将合并后的 Chapter 对象转换为数据库记录
                new_record = chapter_to_record(new_chapter_obj)
                # 更新数据库中的记录
                session.merge(new_record)
            spider.logger.debug(f"已保存章节: {repr(chapter_item)}")
            # 提交事务, 保存更改
            session.commit()