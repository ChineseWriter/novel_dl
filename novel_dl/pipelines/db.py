#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: db.py
# @Time: 03/08/2025 10:21
# @Author: Amundsen Severus Rubeus Bjaaland
"""将经过检查的 BookItem 和 ChapterItem 保存到数据库中."""


# 导入标准库
from collections import defaultdict

# 导入自定义库
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import GeneralSpider
from novel_dl.utils.db_manager import DBManager
from novel_dl.utils.identify import hash_


class DBPipeline:
    """将经过检查的 BookItem 和 ChapterItem 保存到数据库中."""

    def __init__(self) -> None:
        """初始化数据库管道."""
        # 该缓存字典用于存储先于 BookItem 到达的 ChapterItem
        self.chapter_cache: dict[str, list[ChapterItem]] = defaultdict(list)

    def open_spider(self, _: GeneralSpider) -> None:
        """在爬虫开启时调用, 初始化数据库连接."""
        self.db_manager = DBManager()

    def close_spider(self, _: GeneralSpider) -> None:
        """在爬虫关闭时调用, 关闭数据库连接."""
        del self.db_manager

    def process_item(
        self, item: BookItem | ChapterItem, _: GeneralSpider,
    ) -> BookItem | ChapterItem:
        """对传入的 item 进行类型检查和保存."""
        # 判断 Item 的类型, 并依据类型进行处理
        if isinstance(item, BookItem):
            # 将 BookItem 添加到数据库
            self.db_manager.add_book(item)
            # 如果该书籍有缓存的章节, 则一并添加到数据库
            if bool(self.chapter_cache[hash_(item)]):
                for chapter_item in self.chapter_cache[hash_(item)]:
                    self.db_manager.add_chapter(chapter_item)
                del self.chapter_cache[hash_(item)]
        if isinstance(item, ChapterItem) and \
            (not self.db_manager.add_chapter(item)):
            self.chapter_cache[item["book_hash"]].append(item)
        # 返回处理后的 item, 以便后续管道使用
        return item
