#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: convert.py
# @Time: 26/08/2025 08:42
# @Author: Amundsen Severus Rubeus Bjaaland
"""提供实体对象与数据库记录、爬虫 Item 之间的转换功能."""


# 导入标准库
from typing import TYPE_CHECKING, Iterable  # noqa: I001

# 导入自定义库: 用于类型转换
from novel_dl.entity.base import Book, Chapter, Cover
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.entity.models import (
    BookTable, ChapterTable, CoverTable, BookSourceTable, ChapterSourceTable,
)
from novel_dl.settings import IMAGES_STORE
from novel_dl.utils.identify import hash_


if TYPE_CHECKING:
    from pathlib import Path


def item_to_cover(item: BookItem) -> Iterable[Cover]:
    """将 BookItem 内的图片数据转换为 Cover 对象."""
    # 遍历每个封面 URL 和对应的数据, 创建 Cover 对象.
    for source, data in zip(item["cover_urls"], item["covers"], strict=True):
        # 拼接得到封面图片的缓存路径
        file_path: Path = IMAGES_STORE / data["path"]
        # 确认路径上的文件是否存在
        if not file_path.exists(): continue
        # 读取图片文件的二进制数据
        with file_path.open("rb") as image_file:
            image_data = image_file.read()
        # 创建 Cover 对象并返回
        yield Cover(source, image_data)


def record_to_cover(record: CoverTable) -> Cover:
    """将数据库记录转换为 Cover 对象."""
    return Cover(source=record.source, data=record.image)


def cover_to_record(cover: Cover) -> CoverTable:
    """将 Cover 对象转换为数据库记录."""
    return CoverTable(
        cover_hash = hash_(cover),
        source     = cover.source,
        cover      = cover.data,
    )


def item_to_chapter(item: ChapterItem) -> Chapter:
    """将 ChapterItem 转换为 Chapter 对象."""
    return Chapter(
        book_hash   = item["book_hash"],
        index       = item["index"],
        title       = item["title"],
        update_time = item["update_time"],
        content     = item["content"],
        sources     = [item["source"]],
        other_info  = item["other_info"],
    )


def record_to_chapter(record: ChapterTable) -> Chapter:
    """将数据库记录转换为 Chapter 对象."""
    return Chapter(
        book_hash   = record.book_hash,
        index       = record.index,
        title       = record.title,
        update_time = record.update_time,
        content     = record.content,
        sources     = [i.url for i in record.sources],
        other_info  = record.other_info,
    )


def chapter_to_record(chapter: Chapter) -> ChapterTable:
    """将 Chapter 对象转换为数据库记录."""
    return ChapterTable(
        chapter_hash = hash_(chapter),
        index        = chapter.index,
        title        = chapter.title,
        update_time  = chapter.update_time,
        content      = chapter.content,
        other_info   = chapter.other_info,
        book_hash    = chapter.book_hash,
        sources      = [
            ChapterSourceTable(url_hash = hash_(i), url = i)
            for i in chapter.sources
        ],
    )


def item_to_book(item: BookItem) -> Book:
    """将 BookItem 转换为 Book 对象."""
    book_obj = Book(
        title      = item["title"],
        author     = item["author"],
        state      = item["state"],
        desc       = item["desc"],
        tags       = [],
        sources    = [item["source"]],
        other_info = item["other_info"],
    )
    book_obj.covers = list(item_to_cover(item))
    return book_obj


def record_to_book(record: BookTable) -> Book:
    """将数据库记录转换为 Book 对象."""
    book_obj = Book(
        title      = record.title,
        author     = record.author,
        state      = Book.state_shift_2[record.state],
        desc       = record.desc,
        tags       = record.tags,
        sources    = [i.url for i in record.sources],
        other_info = record.other_info,
    )
    book_obj.covers   = [record_to_cover(i)   for i in record.covers  ]
    book_obj.chapters = [record_to_chapter(i) for i in record.chapters]
    return book_obj


def book_to_record(book: Book) -> BookTable:
    """将 Book 对象转换为数据库记录, 注意: 不包含封面和章节数据."""
    return BookTable(
        book_hash  = hash_(book),
        title      = book.title,
        author     = book.author,
        state      = Book.state_shift_1[book.state],
        desc       = book.desc,
        tags       = book.tags,
        other_info = book.other_info,
        sources    = [
            BookSourceTable(url_hash = hash_(i), url = i)
            for i in book.sources
        ],
        covers     = [cover_to_record(i) for i in book.covers],
        chapters   = [chapter_to_record(i) for i in book.chapters],
    )
