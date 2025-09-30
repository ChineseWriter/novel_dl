#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: items.py
# @Time: 14/07/2025 09:59
# @Author: Amundsen Severus Rubeus Bjaaland
"""这是 novel_dl 项目的 Item 模型文件, 用于定义爬虫项目中使用的 Item 模型."""
# 在此定义爬虫项目的 Item 模型, 文档请见:
# https://docs.scrapy.org/en/latest/topics/items.html


# 导入第三方库
import scrapy


# 设置默认的源 URL, 用于爬虫未指定源时的默认值.
DEFAULT_URL = "https://example.com"


class BookItem(scrapy.Item):
    """书籍信息的 Item 模型, 用于存储书籍的基本信息和元数据."""

    # 以下为必填字段, 爬虫必须提供这些信息.
    title      = scrapy.Field(default="Default Book")    # 书籍名称
    author     = scrapy.Field(default="Default Author")  # 书籍作者
    state      = scrapy.Field(default="Unknown")         # 书籍的状态
    desc       = scrapy.Field(default="Default Desc")    # 书籍的简介
    source     = scrapy.Field(default=DEFAULT_URL)       # 书籍的来源
    # 以下为可选字段, 爬虫可以根据需要提供.
    other_info = scrapy.Field(default=None)              # 书籍的其它信息
    cover_urls = scrapy.Field(default=None)              # 书籍封面的 URL 列表
    covers     = scrapy.Field(default=None)              # 书籍封面图片列表

    def __repr__(self) -> str:
        title  = self.get("title", "Unknown")
        author = self.get("author", "Unknown")
        return f"<BookItem title={title} author={author}>"

    @staticmethod
    def default() -> "BookItem":
        """返回一个具有默认值的 BookItem 实例."""
        return BookItem(
            title="Default Book",
            author="Default Author",
            state="Unknown",
            desc="Default Desc",
            source=DEFAULT_URL,
            other_info=None,
            cover_urls=None,
            covers=None,
        )


class ChapterItem(scrapy.Item):
    """章节信息的 Item 模型, 用于存储章节的基本信息和内容."""

    # 以下为必填字段, 爬虫必须提供这些信息.
    book_hash   = scrapy.Field(default="0"*64)               # 章节所属书籍的哈希值
    index       = scrapy.Field(default=-1)                   # 章节的索引
    title       = scrapy.Field(default="Default Chapter")    # 章节的标题
    content     = scrapy.Field(default="Default Content")    # 章节的内容
    source      = scrapy.Field(default=DEFAULT_URL)          # 章节的来源 URL
    # 以下为可选字段, 爬虫可以根据需要提供.
    update_time = scrapy.Field(default=0.0)                  # 章节的更新时间
    other_info  = scrapy.Field(default=None)                   # 章节的其它信息

    def __repr__(self) -> str:
        # 检查所需要显示的字段是否存在, 若不存在则使用默认值.
        index = self.get("index", -1)
        title = self.get("title", "Unknown")
        content_length = len(self["content"]) if ("content" in self) else 0
        # 返回格式化的字符串表示
        return (f"<ChapterItem index={index} title={title} "
            f"content_length={content_length}>")

    @staticmethod
    def default() -> "ChapterItem":
        """返回一个具有默认值的 ChapterItem 实例."""
        return ChapterItem(
            book_hash="0"*64,
            index=-1,
            title="Default Chapter",
            content="Default Content",
            source=DEFAULT_URL,
            update_time=0.0,
            other_info=None,
        )
