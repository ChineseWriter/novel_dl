#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: templates.py
# @Time: 19/07/2025 15:31
# @Author: Amundsen Severus Rubeus Bjaaland


# 导入标准库
import re
from enum import Enum
from urllib.parse import urlparse
from abc import ABC, abstractmethod
from collections.abc import Iterable, AsyncGenerator
# 导入第三方库
from scrapy import Spider
from itemloaders import ItemLoader
from scrapy.http import Response, Request
from itemloaders.processors import TakeFirst, Identity, MapCompose
# 导入自定义库: 自定义的 Scrapy 的 Item 类
from novel_dl.items import BookItem, ChapterItem
# 导入自定义库: 字符串规范化方法
from novel_dl.utils.str_deal import add_tab


class GeneralSpider(Spider, ABC):
    """
    # GeneralSpider
    这是一个通用的 Scrapy 爬虫模板类, 用于定义基本的爬虫结构和方法.
    
    ## 属性
    - name: str
        爬取的网站的名称, 用于 Scrapy 框架识别.
    - domain: str
        爬虫目标网站的域名, 用于构建请求 URL.
    - book_url_pattern: re.Pattern | None
        用于匹配书籍详情页的 URL 模式, 如果为 None 则
        爬虫不会处理书籍详情页.
    - chapter_url_pattern: re.Pattern | None
        用于匹配章节详情页的 URL 模式, 如果为 None 则
        爬虫不会处理章节详情页.
    - Mode: Enum
        枚举类, 定义爬虫的运行模式, 包括列表模式和书籍模式.
    """
    
    # 爬取的网站的名称
    name = "默认网站名"
    # 爬取的网站的域名
    domain = "www.example.com"
    # 网站的书籍详情页 URL 模式
    book_url_pattern = re.compile(r"^/book/\d+/$")
    # 网站的章节详情页 URL 模式
    chapter_url_pattern = re.compile(r"^/book/\d+/chapter/\d+\.html$")
    
    class Mode(Enum):
        """
        # Mode
        枚举类, 定义爬虫的运行模式.
        
        ## 成员
        - LIST: (1, "list")
            列表模式, 爬虫将从网站的首页开始爬取,
            并遍历所有书籍列表.
        - BOOK: (2, "book")
            书籍模式, 爬虫将直接爬取指定的书籍链接,
            并获取书籍的详细信息和章节列表.
        """
        # 列表模式
        LIST = (1, "list")
        # 书籍模式
        BOOK = (2, "book")
    
    def __init__(
        self, novel_url: str = "",
        load_all: bool = False, *args, **kwargs
    ):
        """
        # __init__
        初始化爬虫实例, 设置加载标志, 起始 URL 和运行模式.
        
        加载标志参数用于指定是否在获取列表时下载章节内容,
        运行模式只有两种: 列表模式和书籍模式.
        """
        # 调用父类的初始化方法以确保 Scrapy 框架正确设置爬虫实例.
        super().__init__(*args, **kwargs)
        
        # 初始化加载标志参数, 该参数用于指定是否在获取列表时下载章节内容.
        self.__load_flag = load_all
        
        # 根据 novel_url 参数决定爬虫的起始 URL 和运行模式.
        # 如果指定了小说链接, 则以书籍模式运行, 否则以列表模式运行.
        if novel_url:
            self.__start_url = novel_url
            self.__mode = self.Mode.BOOK
        else:
            self.__start_url = f"https://{self.domain}/"
            self.__mode = self.Mode.LIST

        # 当爬虫以书籍模式运行时, 记录章节数量.
        self.__chapter_count = 0
    
    @property
    def start_url(self) -> str:
        return self.__start_url
    
    @property
    def mode(self) -> Mode:
        return self.__mode
    
    @property
    def load_flag(self) -> bool:
        return self.__load_flag
    
    @property
    def chapter_count(self) -> int:
        return self.__chapter_count
    
    async def start(self) -> AsyncGenerator[Request, None]:
        """
        # start
        爬虫的入口点, 根据爬虫的运行模式决定起始请求以及回调函数.
        """
        # 根据爬虫的运行模式决定起始请求的处理方式
        if self.__mode == self.Mode.LIST:
            self.logger.info("由于未指定小说链接, 爬虫将以列表模式运行!")
            self.logger.info(
                f"由于 load_all 参数为{self.__load_flag}, "
                f"爬虫将{'' if self.__load_flag else '不'}会下载小说内容!"
            )
            # 如果是列表模式, 则从起始 URL 开始爬取书籍列表,
            # 回调函数为 parse_list.
            yield Request(self.__start_url, self.parse_list)
        else:
            self.logger.info("由于指定了小说链接, 爬虫将以书籍模式运行!")
            # 如果是书籍模式, 则直接请求指定的书籍链接,
            # 回调函数为 parse_book.
            yield Request(self.__start_url, self.parse_book)
    
    def parse_list(self, response: Response):
        """
        # parse_list
        解析所有页面(默认不包括章节页面, 仅当 load_flag 为 True 时包括),
        获取书籍信息(仅当 load_flag 为 True 时包括章节页面).
        
        ## 解析流程
        1. 获取当前页面的 URL, 如果是书籍详情页, 则
           调用 get_book_info 方法获取书籍信息.
        2. 如果书籍信息获取成功, 则返回书籍信息,
           并根据 load_flag 决定是否获取章节列表.
        3. 如果章节列表获取成功, 则遍历章节列表并生成请求.
        4. 通过 CSS 选择器获取所有链接, 遍历每一个链接,
           如果链接是 JavaScript 链接则跳过, 否则生成请求
           并返回链接, 准备发送请求.
        """
        # 用作过程执行成功的标志, 包括 book_info 和 chapter_list.
        book_info = None
        chapter_list = None
        
        # 如果当前页面是书籍详情页, 则获取书籍信息.
        if self.book_url_pattern.match(urlparse(response.url).path):
            book_info = self.get_book_info(response)
        # 如果书籍信息获取成功, 则返回书籍信息,
        # 满足条件时也会获取章节列表.
        if book_info is not None:
            yield book_info
            # 根据 load_flag 决定是否获取章节列表.
            if self.load_flag:
                chapter_list = self.get_chapter_list(
                    response, book_info
                )
        # 如果章节列表获取成功, 则遍历章节列表并生成请求.
        if chapter_list is not None:
            for chapter_request in chapter_list:
                chapter_request.priority = 5
                yield chapter_request
        
        # 通过 CSS 选择器获取所有链接.
        all_urls = response.css('a::attr(href)').getall()
        # 遍历每一个链接.
        for url in all_urls:
            # 如果链接是 JavaScript 链接, 则跳过.
            if url.lower().startswith("javascript"): continue
            
            # 获取跟随后的链接
            request = response.follow(url, self.parse_list)
            
            # 如果链接是章节详情页, 则跳过.
            if self.chapter_url_pattern.match(
                urlparse(request.url).path
            ): continue
            
            # 返回链接, 准备发送请求.
            yield request
    
    def parse_book(self, response: Response):
        """
        # parse_book
        解析书籍详情页, 获取书籍信息、封面和章节列表, 进一步获取章节信息.
        """
        # 获取书籍信息, 如果获取失败则返回 None.
        book_info = self.get_book_info(response)
        # 如果书籍信息获取失败, 则记录错误并返回.
        if book_info is None:
            self.logger.error("在该次请求中没有找到书籍信息!")
            return
        # 记录获取到的书籍信息, 并返回书籍信息.
        self.logger.info(
            f"获取到书籍信息：{book_info.get('title', '未知标题')} - "
            f"{book_info.get('author', '未知作者')}"
        )
        yield book_info
        
        # 获取章节列表, 如果获取失败则返回 None.
        chapter_list = self.get_chapter_list(response, book_info)
        # 如果章节列表获取失败, 则记录错误并返回.
        if chapter_list is None:
            self.logger.error("在该次请求中没有找到章节列表!")
            return
        # 将 chapter_list 转为列表以便多次使用.
        chapter_list = list(chapter_list)
        # 记录获取到的章节列表长度.
        self.__chapter_count = len(chapter_list)
        # 遍历章节列表并生成请求.
        yield from chapter_list
    
    @abstractmethod
    def get_book_info(self, response: Response) -> BookItem | None:
        return None
    
    @abstractmethod
    def get_chapter_list(
        self, response: Response, book: BookItem
    ) -> Iterable[Request] | None:
        return None
    
    @abstractmethod
    def get_chapter_info(
        self, response: Response
    ) -> ChapterItem | None:
        return None


class BookItemLoader(ItemLoader):
    default_item_class       = BookItem
    default_output_processor = TakeFirst()
    
    
    title_in       = MapCompose(str.strip)
    author_in      = MapCompose(str.strip)
    state_in       = MapCompose(str.strip)
    desc_in        = MapCompose(str.strip, add_tab)
    source_in      = MapCompose(str.strip)
    
    other_info_in  = Identity()
    cover_urls_in  = MapCompose(str.strip, lambda x: [x,])
    covers_in      = Identity()
    comments_in    = Identity()
    
    
    other_info_out = Identity()
    cover_urls_out = Identity()
    covers_out     = Identity()
    comments_out   = Identity()


class ChapterItemLoader(ItemLoader):
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
