#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: exporters.py
# @Time: 25/08/2025 12:30
# @Author: Amundsen Severus Rubeus Bjaaland


# 导入标准库
from io import BytesIO
from typing import IO

# 导入第三方库: 用于保存 EPUB 文件
from ebooklib import epub

# 导入第三方库: 用于继承定义新的导出器
from scrapy.exporters import BaseItemExporter

# 导入自定义库: 用于类型标注
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.entity.base import Book

# 导入自定义库: 用于类型转换
from novel_dl.utils.convert import item_to_book, item_to_chapter

# 导入自定义库: 用于生成 EPUB 文件
from novel_dl.utils.epub import get_epub


class GenericExporter(BaseItemExporter):
    """
    # GenericExporter
    通用导出器, 仅写出了收集 Item 并转换为 Book 对象的逻辑.
    """
    def __init__(self, file: IO[bytes], **kwargs) -> None:
        # 初始化父类
        super().__init__(**kwargs)
        # 获取文件对象
        self.file = file
        # 初始化存储书籍对象的变量
        self.book: None | Book = None
        # 初始化章节缓存列表
        self.buffer = []
        
    def start_exporting(self) -> None:
        """开始导出"""
        # 将文件指针移动到文件开头
        self.file.seek(0)
        # 截断之后的内容, 清空文件
        self.file.truncate()
    
    def export_item(self, item: BookItem | ChapterItem) -> None:
        """导出单个 Item"""
        # 判断传入的 Item 的类型
        if isinstance(item, BookItem):
            # 如果是 BookItem, 则创建书籍对象
            self.book = item_to_book(item)
            # 将缓存中的 ChapterItem 添加到书籍对象中
            for i in self.buffer:
                # 从 ChapterItem 创建章节对象
                chapter = item_to_chapter(i)
                # 将章节对象添加到书籍对象中
                self.book.append(chapter)
            # 完成 BookItem 的导出
            return None
        # 如果是 ChapterItem, 则判断书籍对象是否已经被创建
        if self.book is None:
            # 如果书籍对象还未被创建, 则将章节缓存到列表中
            self.buffer.append(item)
            # 完成 ChapterItem 的导出
            return None
        # 如果书籍对象已经被创建, 则直接创建章节对象
        chapter = item_to_chapter(item)
        # 将章节对象添加到书籍对象中
        self.book.append(chapter)


class TxtExporter(GenericExporter):
    """
    # TxtExporter
    将小说导出为 TXT 格式的导出器
    """
    def finish_exporting(self) -> None:
        """完成导出"""
        # 确保书籍对象已经被创建
        if self.book is None: return None
        # 对书籍的章节进行排序
        self.book.sort_chapters()
        # 将书籍内容写入文件
        self.file.write(str(self.book).encode("UTF-8"))


class EpubExporter(GenericExporter):
    """
    # EpubExporter
    将小说导出为 EPUB 格式的导出器
    """
    def finish_exporting(self) -> None:
        """完成导出"""
        # 确保书籍对象已经被创建
        if self.book is None: return None
        # 对书籍的章节进行排序
        self.book.sort_chapters()
        # 生成 EPUB 文件对象
        ebook = get_epub(self.book)
        # 创建内存文件
        memory_file = BytesIO()
        # 将 EPUB 内容写入内存文件
        epub.write_epub(memory_file, ebook, {})
        # 保存内存文件
        self.file.write(memory_file.getvalue())