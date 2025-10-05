#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: verify.py
# @Time: 23/08/2025 20:56
# @Author: Amundsen Severus Rubeus Bjaaland
"""验证管道模块."""

# 导入标准库
from collections import defaultdict

# 导入自定义库: 用于类型注解和判断
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import GeneralSpider


class VerifyPipeline:
    """验证管道, 用于验证章节下载完整性."""

    def __init__(self) -> None:
        """初始化方法."""
        # 初始化计数器
        self.counter: defaultdict[str, int] = defaultdict(int)

    def process_item(
        self, item: BookItem, _: GeneralSpider,
    ) -> BookItem | ChapterItem:
        """主要的处理方法.

        处理每个 Item, 如果启用计数功能且当前项是章节, 则计数器加一.
        最后将 Item 返回给下一个 Pipeline.
        """
        # 如果当前项是章节, 则计数器加一
        if isinstance(item, ChapterItem):
            self.counter[item["book_hash"]] += 1
        # 将 Item 返回给下一个 Pipeline
        return item

    def close_spider(self, spider: GeneralSpider) -> None:
        """在爬虫关闭时调用, 如果计数器与章节总数不符, 则记录警告日志."""
        for book_hash, count in self.counter.items():
            ideal_count = spider.chapters_crawled.get(book_hash, 0)
            if count != ideal_count:
                spider.logger.warning(
                    f"书籍未下载完全: {count}/{ideal_count}"
                    f"({(count / ideal_count) * 100:.2f}%) 章节!",
                )
