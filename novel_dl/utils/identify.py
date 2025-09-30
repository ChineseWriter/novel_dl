#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: identify.py
# @Time: 30/09/2025 19:44
# @Author: Amundsen Severus Rubeus Bjaaland
"""该模块用于获取 书籍 及 相关信息 的抽象表示的哈希值."""


# 导入标准库
import hashlib
from typing import Union

# 导入自定义库
from novel_dl.items import BookItem, ChapterItem


# 定义支持的类型
SUPPORTED_TYPES = Union[BookItem,ChapterItem]


def hash_(obj: SUPPORTED_TYPES) -> str:
    """获取对象的唯一哈希值.

    请注意, 该函数传入的对象应该是 小说 或 相关信息的抽象表现,
    如 BookItem, Book 等对象.
    """
    if isinstance(obj, BookItem):
        return book_hash(
            obj.get("title", "Default Book"),
            obj.get("author", "Default Author"),
        )
    elif isinstance(obj, ChapterItem):
        return chapter_hash(
            obj.get("index", -1),
            obj.get("title", "Default Chapter"),
        )
    else:
        return "0" * 64


def chapter_hash(index: int, title: str) -> str:
    """获取章节的唯一哈希值, 由章节索引和章节标题生成."""
    return _hash(f"No.{index} - {title}")


def book_hash(name: str, author: str) -> str:
    """获取书籍的唯一哈希值, 由书名和作者生成."""
    return _hash(f"{name} - {author}")


def _hash(text: str) -> str:
    """获取字符串的 SHA3-256 哈希值. 字符串以 UTF-8 编码."""
    return hashlib.sha3_256(text.encode("UTF-8")).hexdigest()
