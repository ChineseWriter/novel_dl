#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: convert.py
# @Time: 26/08/2025 08:42
# @Author: Amundsen Severus Rubeus Bjaaland


# 导入标准库
import os
from typing import Iterable
# 导入自定义库: 用于类型转换
from novel_dl.entity.items import ChapterItem, BookItem
from novel_dl.entity.base import Cover, Chapter, Book
from novel_dl.entity.models import CoverTable, ChapterTable, ContentTable
from novel_dl.entity.models import BookTable, ExtraInfoTable
# 导入自定义库: 用于读取文件
from novel_dl.settings import IMAGES_STORE


def item_to_cover(item: BookItem) -> Iterable[Cover]:
    """将 BookItem 内的图片数据转换为 Cover 对象"""
    # 遍历每个封面 URL 和对应的数据, 创建 Cover 对象.
    for source, data in zip(item["cover_urls"], item["covers"]):
        # 拼接得到封面图片的缓存路径
        file_path = os.path.join(IMAGES_STORE, data["path"])
        # 确认路径上的文件是否存在
        if not os.path.exists(file_path): continue
        # 读取图片文件的二进制数据
        with open(file_path, "rb") as image_file:
            image_data = image_file.read()
        # 创建 Cover 对象并返回
        yield Cover(source, image_data)


def record_to_cover(record: CoverTable) -> Cover:
    """将数据库记录转换为 Cover 对象"""
    return Cover(source=record.source, data=record.cover)


def cover_to_record(cover: Cover) -> CoverTable:
    """将 Cover 对象转换为数据库记录"""
    return CoverTable(
        cover_hash = cover.hash,
        source     = cover.source,
        cover      = cover.data
    )
    

def item_to_chapter(item: ChapterItem) -> Chapter:
    """将 ChapterItem 转换为 Chapter 对象"""
    return Chapter(
        book_hash   = item["book_hash"],
        index       = item["index"],
        title       = item["title"],
        update_time = item["update_time"],
        content     = item["content"],
        sources     = [item["source"],],
        other_info  = item["other_info"]
    )


def chapter_to_item(chapter: Chapter) -> ChapterItem:
    """将 Chapter 对象转换为 ChapterItem"""
    item = ChapterItem()
    item["book_hash"]   = chapter.book_hash
    item["index"]       = chapter.index
    item["title"]       = chapter.title
    item["content"]     = chapter.content
    item["source"]      = chapter.sources[0]
    item["update_time"] = chapter.update_time
    item["other_info"]  = chapter.other_info
    return item


def record_to_chapter(
    record_info: ChapterTable, record_content: ContentTable
) -> Chapter:
    """将数据库记录转换为 Chapter 对象"""
    return Chapter(
        book_hash   = record_info.book_hash,
        index       = record_info.index,
        title       = record_info.title,
        update_time = record_info.update_time,
        content     = record_content.content,
        sources     = record_content.sources,
        other_info  = record_content.other_info
    )


def chapter_to_record(chapter: Chapter) -> ChapterTable:
    """将 Chapter 对象转换为数据库记录"""
    content_record = ContentTable(
        chapter_hash = chapter.hash,
        content      = chapter.content,
        sources      = chapter.sources,
        other_info   = chapter.other_info
    )
    chapter_record = ChapterTable(
        chapter_hash = chapter.hash,
        index        = chapter.index,
        title        = chapter.title,
        update_time  = chapter.update_time,
        book_hash    = chapter.book_hash
    )
    chapter_record.content = content_record
    return chapter_record


def item_to_book(item: BookItem) -> Book:
    """将 BookItem 转换为 Book 对象"""
    book_obj = Book(
        title      = item["title"],
        author     = item["author"],
        state      = item["state"],
        desc       = item["desc"],
        tags       = [],
        sources    = [item["source"],],
        other_info = item["other_info"]
    )
    covers_obj = list(item_to_cover(item))
    book_obj.covers = covers_obj
    return book_obj


def book_to_item(book: Book) -> BookItem:
    """将 Book 对象转换为 BookItem, 注意: 不包含封面数据"""
    item = BookItem()
    item["title"]      = book.title
    item["author"]     = book.author
    item["state"]      = book.state
    item["desc"]       = book.desc
    item["source"]     = book.sources[0]
    item["other_info"] = book.other_info
    return item


def record_to_book(record: BookTable) -> Book:
    """将数据库记录转换为 Book 对象"""
    book_obj = Book(
        title      = record.title,
        author     = record.author,
        state      = Book.state_shift_2[record.state],
        desc       = record.extra_info.desc,
        tags       = record.extra_info.tags,
        sources    = record.extra_info.sources,
        other_info = record.extra_info.other_info
    )
    book_obj.covers = [record_to_cover(i) for i in record.covers]
    book_obj.chapters = [
        record_to_chapter(i, i.content) for i in record.chapters
    ]
    return book_obj


def book_to_record(book: Book) -> BookTable:
    """将 Book 对象转换为数据库记录, 注意: 不包含封面和章节数据"""
    book_record = BookTable(
        book_hash = book.hash,
        title     = book.title,
        author    = book.author,
        state     = Book.state_shift_1[book.state]
    )
    info_record = ExtraInfoTable(
        book_hash  = book.hash,
        desc       = book.desc,
        tags       = book.tags,
        sources    = book.sources,
        other_info = book.other_info
    )
    cover_records = [cover_to_record(i) for i in book.covers]
    for one_cover in cover_records:
        one_cover.book_hash = book.hash
    book_record.extra_info = info_record
    book_record.covers = cover_records
    return book_record
