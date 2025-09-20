#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: obj.py
# @Time: 08/08/2025 12:16
# @Author: Amundsen Severus Rubeus Bjaaland
"""
# obj
自定义对象类, 用于存储书籍、章节和封面等信息.
"""


# 导入标准库
import os
import time
import copy
from io import BytesIO
# 导入第三方库
from PIL import Image
# 导入自定义库: 获取自定义设置
from novel_dl import settings
# 导入自定义库: 自定义类的哈希函数重写
from novel_dl.utils.str_deal import hash_


# 获取图片存储路径, 如果没有设置则使用默认路径
IMAGES_STORE = settings.IMAGES_STORE \
    if hasattr(settings, "IMAGES_STORE") else "./data/cache/images"


class Cover:
    """
    # Cover
    封面类, 用于存储书籍封面信息.
    
    ## 属性
    - `source`: 封面来源, 如网站名称或图片链接.
    - `data`: 封面图片的二进制数据.
    - `image`: PIL.Image 对象, 用于处理图片.
    """
    def __init__(self, source: str, data: bytes) -> None:
        # 初始化封面对象
        self.source = source
        self.data = data
        self.image = Image.open(BytesIO(data))
    
    def __repr__(self):
        return f"<Cover length={len(self.data)} source={self.source}>"
    
    @property
    def hash(self):
        """
        # hash
        计算封面的哈希值, 用于唯一标识该封面. 返回一个长度为 64 的字符串.
        
        ## 计算方法
        使用封面来源的字符串进行哈希计算, 确保每个封面都有唯一的标识符.
        """
        return hash_(self.source)
    
    def to_jpg(self) -> None:
        """
        # to_jpg
        将图片转换为 JPG 格式
        """
        # 确认图片是否存在透明通道
        if self.image.mode in ("RGBA", "P"):
            # 创建一个白色背景
            background = Image.new("RGB", self.image.size, (255, 255, 255))
            # 将原图粘贴上去, 其中遮罩设置为透明通道
            background.paste(self.image, mask=self.image.split()[-1])
            # 获取新的图片
            self.image = background
        # 创建内存中文件
        memory_file = BytesIO()
        # 将图片保存
        self.image.save(memory_file, format="JPEG", quality=95)
        # 将图片原值改变为内存文件的内容
        self.data = memory_file.getvalue()


class Chapter:
    """
    # Chapter
    章节类, 用于存储书籍章节信息.
    
    ## 属性
    - `book_hash`: 书籍的唯一标识符, 用于关联章节和书籍.
    - `index`: 章节的索引, 从 1 开始.
    - `title`: 章节标题.
    - `update_time`: 章节的最后更新时间, 使用时间戳表示.
    - `content`: 章节内容.
    - `sources`: 章节内容的来源列表.
    - `other_info`: 章节的其他信息.
    """
    def __init__(
        self, book_hash: str, index: int,
        title: str, update_time: float, content: str,
        sources: list[str], other_info: dict
    ):
        # 初始化章节对象
        self.book_hash = book_hash
        self.index = index
        self.title = title
        self.update_time = update_time
        self.content = content
        self.sources = sources
        self.other_info = other_info
    
    def __repr__(self):
        return f"<Chapter index={self.index} title={self.title}>"
    
    def __str__(self):
        if self.update_time:
            return f"第{str(self.index).rjust(5, '0')}章 {self.title}\n" \
                f"更新时间: {self.update_time_str}\n" \
                f"{self.content}\n\n"
        return f"第{str(self.index).rjust(5, '0')}章 {self.title}\n" \
            f"{self.content}\n\n"
        
    
    def __add__(self, other: "Chapter") -> "Chapter":
        # 确认两个章节对象是否可以合并, 即判断两个章节对象指代的数据是否相同
        if self.hash != other.hash:
            raise ValueError("将章节对象合并时, 要求两者的 hash 相同.")
        # 创建一个新的章节对象, 以便合并两个章节对象
        new_chapter = copy.deepcopy(self)
        # 如果两个章节的更新时间不同, 取较新的更新时间
        if self.update_time < other.update_time:
            new_chapter.update_time = other.update_time
        # 如果两个章节的内容长度不同, 取较长的内容
        if len(self.content) < len(other.content):
            new_chapter.content = other.content
        # 合并章节的来源, 使用 set 去重
        new_chapter.sources = list(set(self.sources + other.sources))
        # 合并章节的其他信息, 将不存在的键添加到新章节中
        for key, item in other.other_info.items():
            if key not in new_chapter.other_info:
                new_chapter.other_info[key] = item
        # 返回合并后的新章节对象
        return new_chapter
    
    @property
    def hash(self) -> str:
        """
        # hash
        计算章节的哈希值, 用于唯一标识该章节. 返回一个长度为 64 的字符串.
        
        ## 计算方法
        使用书籍的哈希值、章节索引和章节标题进行哈希计算,
        确保每个章节都有唯一的标识符.
        """
        return hash_(
            f"书籍({self.book_hash})的"
            f"第{str(self.index).rjust(5, '0')}章 "
            f"-> {self.title}"
        )
    
    @property
    def update_time_str(self) -> str:
        """
        # update_time_str
        将章节的更新时间转换为可读的字符串格式. 具体为 "YYYY-MM-DD HH:MM:SS".
        """
        return time.strftime(
            "%Y-%m-%d %H:%M:%S",
            time.localtime(self.update_time)
        )


class Book:
    """
    # Book
    书籍类, 用于存储书籍的基本信息和相关内容.
    
    ## 属性
    - `title`: 书名.
    - `author`: 作者名.
    - `state`: 书籍状态, 如 "连载", "完结", "断更", "未知".
    - `desc`: 书籍简介.
    - `tags`: 书籍标签列表.
    - `sources`: 书籍来源列表.
    - `other_info`: 书籍的其他信息.
    - `covers`: 书籍封面列表, 包含多个 Cover 对象.
    - `chapters`: 书籍章节列表, 包含多个 Chapter 对象.
    """
    state_shift_1 = {"未知": 0, "断更": 1, "连载": 2, "完结": 3}
    state_shift_2 = {0: "未知", 1: "断更", 2: "连载", 3: "完结"}
    
    def __init__(
        self, title: str, author: str, state: str, desc: str,
        tags: list[str], sources:list[str], other_info:dict
    ):
        # 初始化书籍对象
        self.title = title
        self.author = author
        self.state = state
        self.desc = desc
        self.tags = tags
        self.sources = sources
        self.other_info = other_info
        self.covers: list[Cover] = []
        self.chapters: list[Chapter] = []
    
    def __repr__(self):
        return f"<Book title={self.title} author={self.author}>"
    
    def __str__(self):
        tag_text = ""
        if self.tags:
            tag_text = f"标签: {'、'.join(self.tags)}\n"
        return f"《{self.title}》\n" \
            f"作者: {self.author}\n" \
            f"{tag_text}\n" \
            f"状态: {self.state}\n" \
            f"简介: \n{self.desc}\n\n" \
            f"{''.join([str(i) for i in self.chapters])}"
    
    def __add__(self, other: "Book") -> "Book":
        # 确认两个书籍对象是否可以合并, 即判断两个书籍对象指代的数据是否相同
        if self.hash != other.hash:
            raise ValueError("将书籍对象合并时, 要求两者的 hash 相同.")
        # 创建一个新的书籍对象, 以便合并两个书籍对象
        new_book = copy.deepcopy(self)
        # 如果两本书籍的状态不同, 取较高优先级的状态
        if self.state_shift_1[self.state] < self.state_shift_1[other.state]:
            new_book.state = other.state
        # 如果两本书籍的简介长度不同, 取较长的简介
        if len(self.desc) < len(other.desc):
            new_book.desc = other.desc
        # 合并书籍的标签和来源, 使用 set 去重
        new_book.tags = list(set(self.tags + other.tags))
        new_book.sources = list(set(self.sources + other.sources))
        # 合并书籍的其他信息, 将不存在的键添加到新书籍中
        for key, item in other.other_info.items():
            if key not in new_book.other_info:
                new_book.other_info[key] = item
        # 合并书籍的封面, 使用对象的 hash 值确保不重复
        cover_hashes = [i.hash for i in self.covers]
        for one_cover in other.covers:
            if one_cover.hash not in cover_hashes:
                new_book.covers.append(one_cover)
        # 合并书籍的章节, 使用对象的 hash 值确保不重复
        chapter_hashes = [i.hash for i in self.chapters]
        for one_chapter in other.chapters:
            if one_chapter.hash not in chapter_hashes:
                new_book.chapters.append(one_chapter)
        # 对合并后的章节进行排序, 按照章节索引升序排列
        new_book.chapters.sort(key=lambda x: x.index)
        # 返回合并后的新书籍对象
        return new_book
    
    @property
    def hash(self) -> str:
        """
        # hash
        计算书籍的哈希值, 用于唯一标识该书籍. 返回一个长度为 64 的字符串.
        
        ## 计算方法
        使用书名和作者名进行哈希计算, 确保每本书籍都有唯一的标识符.
        """
        return hash_(f"{self.title} - {self.author}")
    
    @property
    def update_time(self) -> float:
        """
        # update_time
        获取书籍的最新更新时间, 即最后更新的章节的更新时间. 
        如果书籍没有章节, 则返回 0.0. 该方法会对章节排序.
        """
        # 检查书籍是否有章节, 如果没有则返回 0.0
        if not self.chapters: return 0.0
        # 对章节进行排序
        self.sort_chapters()
        # 返回最后一个章节的更新时间
        return self.chapters[-1].update_time
    
    @property
    def update_time_str(self) -> str | None:
        """
        # update_time_str
        获取书籍的更新时间, 即最后更新的章节的更新时间. 
        如果书籍没有章节, 则返回 None. 该方法会对章节排序.
        """
        # 检查书籍是否有章节, 如果没有则返回 None.
        if not self.chapters: return None
        # 对章节进行排序
        self.sort_chapters()
        # 返回最后一个章节的更新时间
        return self.chapters[-1].update_time_str
    
    @property
    def main_cover(self) -> None | Cover:
        """获取书籍的主封面, 逻辑为选取面积最大的一张."""
        # 中间变量, 用于存储主封面和最大面积以进行比较
        cover = None
        size = 0
        for i in self.covers:
            # 获取图片的尺寸
            width, height = i.image.size
            # 计算面积
            image_size = width * height
            # 如果面积更大, 则更新主封面
            if image_size > size:
                cover = i
                size = image_size
        # 返回主封面对象
        return cover

    def append(self, chapter: Chapter) -> None:
        """向书籍对象中添加章节. 如果章节已经存在, 则合并章节信息."""
        # 遍历现有章节
        for index, one_chapter in enumerate(self.chapters):
            # 如果章节已经存在, 则合并章节信息
            if one_chapter.hash == chapter.hash:
                self.chapters[index] = one_chapter + chapter
                return None
        # 如果章节不存在, 则直接添加章节
        self.chapters.append(chapter)
    
    def sort_chapters(self) -> None:
        """对书籍的章节进行排序, 按照章节索引升序排列."""
        self.chapters.sort(key=lambda x: x.index)
