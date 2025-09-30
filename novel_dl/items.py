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
DEFAULT_URL = "https://www.example.com/"


class BookItem(scrapy.Item):
    """书籍信息的 Item 模型, 用于存储书籍的基本信息和元数据."""

    # 以下为必填字段, 爬虫必须提供这些信息.
    title      = scrapy.Field()  # 名称
    author     = scrapy.Field()  # 作者
    state      = scrapy.Field()  # 状态
    desc       = scrapy.Field()  # 简介
    source     = scrapy.Field()  # 来源
    # 以下为可选字段, 爬虫可以根据需要提供.
    other_info = scrapy.Field()  # 其它信息
    cover_urls = scrapy.Field()  # 封面的 URL 列表
    covers     = scrapy.Field()  # 封面图片信息列表(注意不是图片本身)

    def __repr__(self) -> str:
        title  = self.get("title",  "Unknown")
        author = self.get("author", "Unknown")
        return f"<BookItem title={title} author={author}>"

    @staticmethod
    def default() -> "BookItem":
        """返回一个具有默认值的 BookItem 实例."""
        return BookItem(
            title      ="Default Book",
            author     ="Default Author",
            state      ="Unknown",
            desc       ="Default Desc",
            source     =DEFAULT_URL,
            other_info =None,
            cover_urls =None,
            covers     =None,
        )


class ChapterItem(scrapy.Item):
    """章节信息的 Item 模型, 用于存储章节的基本信息和内容."""

    # 以下为必填字段, 爬虫必须提供这些信息.
    book_hash   = scrapy.Field()  # 所属书籍的哈希值
    index       = scrapy.Field()  # 索引
    title       = scrapy.Field()  # 标题
    content     = scrapy.Field()  # 内容
    source      = scrapy.Field()  # 来源
    # 以下为可选字段, 爬虫可以根据需要提供.
    update_time = scrapy.Field()  # 更新时间
    other_info  = scrapy.Field()  # 其它信息

    def __repr__(self) -> str:
        index = self.get("index", -1)
        title = self.get("title", "Unknown")
        content_length = len(self.get("content", ""))
        return (f"<ChapterItem index={index} title={title} "
            f"content_length={content_length}>")

    @staticmethod
    def default() -> "ChapterItem":
        """返回一个具有默认值的 ChapterItem 实例."""
        return ChapterItem(
            book_hash   ="0"*64,
            index       =-1,
            title       ="Default Chapter",
            content     ="Default Content",
            source      =DEFAULT_URL,
            update_time =0.0,
            other_info  =None,
        )
