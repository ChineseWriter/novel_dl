#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: templates.py
# @Time: 19/07/2025 15:31
# @Author: Amundsen Severus Rubeus Bjaaland
"""该模块定义了通用的爬虫模板和 ItemLoader 模板, 用于减少编写具体 Spider 的代码量."""


# 导入标准库
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator, Generator, Iterable
from enum import Enum
from urllib.parse import urlparse

# 导入第三方库
from itemloaders import ItemLoader
from itemloaders.processors import Identity, MapCompose, TakeFirst
from scrapy import Spider
from scrapy.http import Request, Response

# 导入自定义库: 自定义的 Scrapy 的 Item 类
from novel_dl.items import BookItem, ChapterItem

# 导入自定义库: 字符串规范化方法
from novel_dl.utils.str_deal import add_tab


class GeneralSpider(Spider, ABC):
    """这是一个通用的 Scrapy 爬虫模板类, 用于定义基本的爬虫结构和方法."""

    # 爬取的网站的名称
    name = "默认网站名"
    # 爬取的网站的域名
    domain = "www.example.com"
    # 网站的书籍详情页 URL 模式
    book_url_pattern = re.compile(r"^/book/\d+/$")
    # 网站的章节详情页 URL 模式
    chapter_url_pattern = re.compile(r"^/book/\d+/chapter/\d+\.html$")

    class Mode(Enum):
        """枚举类, 定义爬虫的运行模式."""

        # 列表模式, 爬虫将从网站的首页开始爬取, 并遍历所有书籍列表.
        LIST = (1, "list")
        # 书籍模式, 爬虫将直接爬取指定的书籍链接, 并获取书籍的详细信息和章节列表.
        BOOK = (2, "book")

    def __init__(self, novel_url: str | None = None) -> None:
        """初始化爬虫实例, 设置加载标志, 起始 URL 和运行模式.

        加载标志参数用于指定是否在获取列表时下载章节内容,
        运行模式只有两种: 列表模式和书籍模式.
        """
        # 调用父类的初始化方法以确保 Scrapy 框架正确设置爬虫实例.
        super().__init__()

        # 根据 novel_url 参数决定爬虫的起始 URL 和运行模式.
        # 如果指定了小说链接, 则以书籍模式运行, 否则以列表模式运行.
        if novel_url is None:
            self.start_url = f"https://{self.domain}/"
            self.mode = self.Mode.LIST
        else:
            self.start_url = novel_url
            self.mode = self.Mode.BOOK

    async def start(self) -> AsyncGenerator[Request, None]:
        """爬虫的入口点, 根据爬虫的运行模式决定起始请求以及回调函数."""
        # 根据爬虫的运行模式决定起始请求的处理方式
        match self.mode:
            # 如果是列表模式, 则从起始 URL 开始爬取书籍列表, 回调函数为 parse_list.
            case self.Mode.LIST:
                self.logger.info("由于未指定小说链接, 爬虫将以列表模式运行!")
                yield Request(self.start_url, self.parse_list)
            # 如果是书籍模式, 则直接请求指定的书籍链接, 回调函数为 parse_book.
            case self.Mode.BOOK:
                self.logger.info("由于指定了小说链接, 爬虫将以书籍模式运行!")
                yield Request(self.start_url, self.parse_book)

    def parse_list(
            self, response: Response,
        ) -> Generator[Request | BookItem, None, None]:
        """解析所有页面, 获取书籍信息."""
        # 用作过程执行成功的标志, 包括 book_info 和 chapter_list.
        book_info = None
        chapter_list = None

        # 如果当前页面是书籍详情页, 则获取书籍信息.
        if self.book_url_pattern.match(urlparse(response.url).path):
            book_info = self.get_book_info(response)
        # 如果书籍信息获取成功, 则获取章节列表并返回书籍信息.
        if book_info is not None:
            chapter_list = self.get_chapter_list(response, book_info)
            yield book_info
        # 如果章节列表获取成功, 则遍历章节列表并生成请求.
        if chapter_list is not None:
            for chapter_request in chapter_list:
                chapter_request.priority = 5
                yield chapter_request

        # 通过 CSS 选择器获取所有链接.
        all_urls = response.css("a::attr(href)").getall()
        # 遍历每一个链接.
        for url in all_urls:
            # 如果链接是 JavaScript 链接, 则跳过.
            if url.lower().startswith("javascript"): continue
            # 获取跟随后的链接
            request = response.follow(url, self.parse_list)
            # 如果链接是章节详情页, 则跳过.
            if self.chapter_url_pattern.match(
                urlparse(request.url).path,
            ): continue
            # 返回链接, 准备发送请求.
            yield request

    def parse_book(
            self, response: Response,
        ) -> Generator[Request | BookItem, None, None]:
        """解析书籍详情页, 获取书籍信息、封面和章节列表, 进一步获取章节信息."""
        # 获取书籍信息, 如果获取失败则返回 None.
        book_info = self.get_book_info(response)
        # 如果书籍信息获取失败, 则记录错误并返回.
        if book_info is None:
            self.logger.error("在该次请求中没有找到书籍信息!")
            return None
        # 记录获取到的书籍信息, 并返回书籍信息.
        self.logger.info(
            f"获取到书籍信息: {book_info.get('title', '未知标题')} - "
            f"{book_info.get('author', '未知作者')}",
        )
        yield book_info

        # 获取章节列表, 如果获取失败则返回 None.
        chapter_list = self.get_chapter_list(response, book_info)
        # 如果章节列表获取失败, 则记录错误并返回.
        if chapter_list is None:
            self.logger.error("在该次请求中没有找到章节列表!")
            return None
        # 将 chapter_list 转为列表以便多次使用.
        chapter_list = list(chapter_list)
        # 遍历章节列表并生成请求.
        yield from chapter_list

    @abstractmethod
    def get_book_info(self, response: Response) -> BookItem | None:
        """获取书籍的基本信息, 返回 BookItem 实例, 如果获取失败则返回 None."""
        return None

    @abstractmethod
    def get_chapter_list(
        self, response: Response, book: BookItem,
    ) -> Iterable[Request] | None:
        """获取章节列表, 返回章节请求的可迭代对象, 如果获取失败则返回 None."""
        return None

    @abstractmethod
    def get_chapter_info(self, response: Response) -> ChapterItem | None:
        """获取章节的基本信息和内容, 返回 ChapterItem 实例, 如果获取失败则返回 None."""
        return None


class BookItemLoader(ItemLoader):
    """用于加载和处理 BookItem 的 ItemLoader 模板类."""

    default_item_class       = BookItem
    default_output_processor = TakeFirst()

    title_in       = MapCompose(str.strip)
    author_in      = MapCompose(str.strip)
    state_in       = MapCompose(str.strip)
    desc_in        = MapCompose(str.strip, add_tab)
    source_in      = MapCompose(str.strip)

    other_info_in  = Identity()
    cover_urls_in  = Identity()
    covers_in      = Identity()
    comments_in    = Identity()

    other_info_out = Identity()
    cover_urls_out = Identity()
    covers_out     = Identity()
    comments_out   = Identity()


class ChapterItemLoader(ItemLoader):
    """用于加载和处理 ChapterItem 的 ItemLoader 模板类."""

    default_item_class       = ChapterItem
    default_output_processor = TakeFirst()

    book_hash_in   = MapCompose(str.strip)
    index_in       = MapCompose(int)
    title_in       = MapCompose(str.strip)
    content_in     = MapCompose(str.strip)
    source_in      = MapCompose(str.strip)

    update_time_in = MapCompose(float)
    other_info_in  = Identity()
    comments_in    = Identity()

    other_info_out = Identity()
    comments_out   = Identity()
