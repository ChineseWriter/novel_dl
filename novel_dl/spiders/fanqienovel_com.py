#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: fanqienovel_com.py
# @Time: 10/10/2025 18:26
# @Author: Amundsen Severus Rubeus Bjaaland
"""fanqienovel.com 小说爬虫."""

# 导入标准库
import re
import time
from typing import Iterable

# 导入第三方库
from itemloaders.processors import MapCompose
from scrapy.http import Request, Response

# 导入自定义库
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import BookItemLoader, GeneralSpider
from novel_dl.templates import ChapterItemLoader as CIL
from novel_dl.utils.str_deal import get_text_after_space


def convert_time_str(time_str: str) -> float:
    """将时间字符串转换为时间戳."""
    section = time_str.split("-")
    if len(section) != 3:
        time_str = f"{time.strftime('%Y', time.localtime())}-{time_str}"
    return time.mktime(time.strptime(time_str, "%Y-%m-%d"))


class ChapterItemLoader(CIL):
    """章节信息数据加载器."""

    title_in = MapCompose(str.strip, get_text_after_space)
    update_time_in = MapCompose(
        str.strip, convert_time_str, float,
    )


class FanqieSpider(GeneralSpider):
    """fanqienovel.com 小说爬虫.

    请注意: 由于技术原因, 该 Spider 仅提供信息的抓取, 不下载章节内容.
    """

    name = "fanqienovel_com"
    domain = "fanqienovel.com"
    book_url_pattern = re.compile(r"^/page/\d+$")
    chapter_url_pattern = re.compile(r"^/reader/\d+$")

    custom_settings = {
        "AUTOTHROTTLE_TARGET_CONCURRENCY": "0.5",
    }

    def __init__(self, novel_url: str | None = None) -> None:
        """初始化爬虫实例."""
        super().__init__(novel_url)
        self.logger.warning(
            "由于技术原因, 该 Spider 仅提供信息的抓取, 不下载章节内容.",
        )

    def get_book_info(self, response: Response) -> BookItem | None:
        """获取书籍信息."""
        # 获取整个 HTML 页面
        html = self.get_html(response)
        if html is None: return None
        # 使用 ItemLoader 提取书籍信息
        loader = BookItemLoader(item=BookItem(), selector=html)
        loader.add_xpath("title", "//h1[1]/text()")
        loader.add_xpath("author", '//span[@class="author-name-text"][1]/text()')
        loader.add_xpath("cover_urls", '//img[@class="book-cover-img"]/@src')
        loader.add_xpath("state", '//div[@class="info-label"]/span[1]/text()')
        loader.add_xpath("desc", '//div[@class="page-abstract-content"]/p/text()')
        loader.add_value("source", response.url)
        loader.add_value("other_info", {"fq_id": response.url.split("/")[-1]})
        item = loader.load_item()
        # 将 other_info 从列表转换为单个字典
        if isinstance(item["other_info"], list):
            item["other_info"] = item["other_info"][0]
        # 返回书籍信息
        return item

    def get_chapter_list(self, response: Response) -> Iterable[str] | None:
        """获取章节列表."""
        yield from response.xpath(
            '//div[@class="page-directory-content"]//a/@href',
        ).getall()

    def get_chapter_info(  # type: ignore[reportIncompatibleMethodOverride]
            self, response: Response,
        ) -> ChapterItem | Request | None:
        """获取章节信息."""
        # 获取整个 HTML 页面
        html = self.get_html(response)
        if html is None: return None
        # 使用 ItemLoader 提取章节信息
        loader = ChapterItemLoader(item=ChapterItem(), selector=html)
        loader.add_value("book_hash", response.meta["book_hash"])
        loader.add_value("index", response.meta["index"])
        loader.add_xpath("title", '//h1[@class="muye-reader-title"]/text()')
        loader.add_value("content", "占位文本")
        loader.add_value("source", response.url)
        loader.add_xpath(
            "update_time",
            '//div[@class="muye-reader-subtitle"]'
            '//span[@class="desc-item"][2]/text()',
        )
        item = loader.load_item()
        # 记录日志并返回章节信息
        self.logger.debug(
            f"获取到章节信息: {item.get('index', 0)}."
            f"{item.get('title', '未知章节')}",
        )
        return item
