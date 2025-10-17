#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: templates.py
# @Time: 19/07/2025 15:31
# @Author: Amundsen Severus Rubeus Bjaaland
"""该模块定义了通用的爬虫模板和 ItemLoader 模板, 用于减少编写具体 Spider 的代码量."""


# 导入标准库
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import AsyncGenerator, Generator, Iterable
from enum import Enum
from urllib.parse import urlparse

# 导入第三方库
from itemloaders import ItemLoader
from itemloaders.processors import Identity, MapCompose, TakeFirst
from parsel.selector import Selector
from scrapy import Spider
from scrapy.http import Request, Response

# 导入自定义库
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.utils.identify import hash_
from novel_dl.utils.str_deal import add_tab, normalize_book_status


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
    # 是否支持列表模式
    list_mode_supported = False

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
            if not self.list_mode_supported:
                raise ValueError(
                    "该爬虫不支持列表模式, 请指定小说链接以启用书籍模式!",
                )
        else:
            self.start_url = novel_url
            self.mode = self.Mode.BOOK

        # 记录在书籍模式下爬取的书籍的章节数.
        self.chapter_list_flag: defaultdict[str, bool] = defaultdict(bool)
        self.chapters_crawled: defaultdict[str, int] = defaultdict(int)

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
            try: book_info = self.get_book_info(response)
            except Exception as e:  # noqa: BLE001
                self.logger.error(f"获取书籍信息时发生错误: {e}")
        # 如果书籍信息获取成功, 则获取章节列表并返回书籍信息.
        if book_info is not None:
            response.meta["book_hash"] = hash_(book_info)
            response.meta["index"] = 1
            try: chapter_list = self.transform(response)
            except Exception as e:  # noqa: BLE001
                self.logger.error(f"获取章节列表时发生错误: {e}")
            yield book_info
        # 如果章节列表获取成功, 则遍历章节列表并生成请求.
        if chapter_list is not None:
            yield from chapter_list

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
        try: book_info = self.get_book_info(response)
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"获取书籍信息时发生错误: {e}")
            return None
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
        response.meta["book_hash"] = hash_(book_info)
        response.meta["index"] = 1
        try: chapter_list = self.transform(response)
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"获取章节列表时发生错误: {e}")
            return None
        # 如果章节列表获取失败, 则记录错误并返回.
        if chapter_list is None:
            self.logger.error("在该次请求中没有找到章节列表!")
            return None
        # 遍历章节列表, 生成章节请求.
        yield from chapter_list

    def transform(
            self, response: Response,
        ) -> None | Generator[Request, None, None]:
        """转换章节列表页面, 获取章节列表并生成章节请求."""
        # 获取章节列表
        result = self.get_chapter_list(response)
        # 如果章节列表获取失败, 则返回 None.
        if result is None: return None

        # 取出用于传递章节索引的变量
        index: int = response.meta["index"]
        # 检查链接列表中是否存在章节详情页链接
        content_request: Request | None = None
        # 遍历章节列表, 生成章节请求.
        for i in result:
            # 如果链接不是章节详情页, 则将其作为新的章节列表请求返回.
            if not self.chapter_url_pattern.match(i):
                content_request = response.follow(
                    i, self.transform, priority=10,
                    meta={"book_hash": response.meta["book_hash"]},
                )
                continue
            # 如果链接是章节详情页, 则生成章节请求.
            request = response.follow(
                i, self.get_chapter_info, priority=5,
                meta={
                    "book_hash": response.meta["book_hash"],
                    "index": index,
                },
            )
            self.chapters_crawled[response.meta["book_hash"]] += 1
            index += 1
            yield request

        # 如果所有链接均为章节详情页, 则将 chapter_list_flag 设为 True.
        if content_request is None:
            self.chapter_list_flag[response.meta["book_hash"]] = True
            self.logger.info(
                f"书籍 {response.meta['book_hash'][:8]} 的章节列表获取完成, "
                f"共计 {self.chapters_crawled[response.meta['book_hash']]} 章.",
            )
        # 如果章节列表中存在新的章节列表请求, 则将其返回.
        else:
            content_request.meta["index"] = index
            yield content_request

    def get_html(self, response: Response) -> Selector | None:
        """获取并返回响应的 HTML 内容."""
        # 获取整个 HTML 页面
        html = response.xpath("/*")
        # 检查是否成功获取
        if len(html) != 1:
            self.logger.error("在该次请求中没有找到 HTML 元素")
            return None
        # 成功获取 HTML 页面则返回 Selector 对象
        return html[0]

    @abstractmethod
    def get_book_info(self, response: Response) -> BookItem | None:
        """获取书籍的基本信息, 返回 BookItem 实例, 如果获取失败则返回 None."""
        return None

    @abstractmethod
    def get_chapter_list(self, response: Response) -> Iterable[str] | None:
        """获取章节列表.

        返回章节请求的可迭代对象, 或新的章节列表请求, 如果获取失败则返回 None.
        """
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
    state_in       = MapCompose(str.strip, normalize_book_status)
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
