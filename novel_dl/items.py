#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: items.py
# @Time: 14/07/2025 09:59
# @Author: Amundsen Severus Rubeus Bjaaland
"""
# novel_dl.items
这是 novel_dl 项目的 Item 模型文件, 用于定义爬虫项目中使用的 Item 模型.

## Item 模型
1. BookItem: 用于存储书籍的基本信息和元数据.
2. ChapterItem: 用于存储章节的基本信息和内容.
"""
# 在此定义爬虫项目的 Item 模型, 文档请见:
# https://docs.scrapy.org/en/latest/topics/items.html


# 导入第三方库
import scrapy

# 导入自定义库
from novel_dl.utils.str_deal import hash_


# 设置默认的源 URL, 用于爬虫未指定源时的默认值.
DEFAULT_URL = "https://example.com"


class BookItem(scrapy.Item):
    """
    # BookItem
    书籍信息的 Item 模型, 用于存储书籍的基本信息和元数据.
    """
    # 以下为必填字段, 爬虫必须提供这些信息.
    title      = scrapy.Field(default="默认书籍名")   # 书籍名称
    author     = scrapy.Field(default="默认作者")     # 书籍作者
    state      = scrapy.Field(default="未知")        # 书籍的状态
    desc       = scrapy.Field(default="默认书籍简介") # 书籍的简介
    source     = scrapy.Field(default=DEFAULT_URL)  # 书籍的来源
    # 以下为可选字段, 爬虫可以根据需要提供.
    other_info = scrapy.Field(default={})           # 书籍的其它信息
    cover_urls = scrapy.Field(default=[])           # 书籍封面的 URL 列表
    covers     = scrapy.Field(default=[])           # 书籍封面图片列表

    def __repr__(self) -> str:
        title = "未知书籍" if "title" not in self else self["title"]
        author = "未知作者" if "author" not in self else self["author"]
        return f"<BookItem title={title} author={author}>"

    @property
    def book_hash(self) -> str:
        return hash_(f"{self["title"]} - {self["author"]}")


class ChapterItem(scrapy.Item):
    """
    # ChapterItem
    章节信息的 Item 模型, 用于存储章节的基本信息和内容.
    """
    # 以下为必填字段, 爬虫必须提供这些信息.
    book_hash   = scrapy.Field(default="0"*64)        # 章节所属书籍的哈希值
    index       = scrapy.Field(default=-1)            # 章节的索引
    title       = scrapy.Field(default="默认章节名")    # 章节的标题
    content     = scrapy.Field(default="默认章节内容")  # 章节的内容
    source      = scrapy.Field(default=DEFAULT_URL)   # 章节的来源 URL
    # 以下为可选字段, 爬虫可以根据需要提供.
    update_time = scrapy.Field(default=0.0)           # 章节的更新时间
    other_info  = scrapy.Field(default={})            # 章节的其它信息

    def __repr__(self) -> str:
        index = self["index"] if "index" in self else -1
        title = self["title"] if "title" in self else "未知章节"
        content_length = len(self["content"]) if "content" in self else 0
        return f"<ChapterItem index={index} title={title} " \
            f"content_length={content_length}>"
