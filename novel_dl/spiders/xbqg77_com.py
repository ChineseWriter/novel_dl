#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: xbqg77_com.py
# @Time: 25/10/2025 14:59
# @Author: Amundsen Severus Rubeus Bjaaland
"""xbqg77.com 小说爬虫."""


import re
from typing import Iterable

from itemloaders.processors import MapCompose
from scrapy.http import Response

from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import BookItemLoader as BIL
from novel_dl.templates import ChapterItemLoader as CIL
from novel_dl.templates import GeneralSpider
from novel_dl.utils.str_deal import get_text_after_colon, get_text_after_space, normalize_book_status


def deal_content(content: str) -> str:
    """处理章节内容."""
    # 确保内容长度, 防止出现 index out of range 错误
    if len(content) < 55: return content
    # 除去多余标签和空格
    data = content[31:-22]
    data = data.replace("\xa0", "")
    data = data.replace("<br>", "\n")
    # 除去多余空行
    data = data.split("\n")
    data = list(filter(lambda x: bool(x.strip()), data))
    return "\n".join(f"\t{x.strip()}" for x in data)


class BookItemLoader(BIL):
    """xbqg77.com 书籍信息加载器."""

    author_in = MapCompose(get_text_after_colon, str.strip)
    state_in = MapCompose(
        get_text_after_colon, str.strip, normalize_book_status,
    )
    desc_in = MapCompose(str.strip, lambda x: x.replace(" ", ""))


class ChapterItemLoader(CIL):
    """xbqg77.com 章节信息加载器."""

    title_in = MapCompose(str.strip, get_text_after_space)
    content_in = MapCompose(str.strip, deal_content)


class Xbqg77Spider(GeneralSpider):
    """xbqg77.com 小说爬虫."""

    name = "xbqg77_com"
    domain = "www.xbqg77.com"
    book_url_pattern = re.compile(r"^/\d+$")
    chapter_url_pattern = re.compile(r"^/\d+/\d+$")
    list_mode_supported = True

    def get_book_info(self, response: Response) -> BookItem | None:
        """获取书籍信息."""
        # 获取整个 HTML 页面
        html = self.get_html(response)
        if html is None: return None
        # 使用 ItemLoader 提取书籍信息
        loader = BookItemLoader(item=BookItem(), selector=html)
        loader.add_xpath("title", '//div[@class="title"]/text()')
        loader.add_xpath("author", '//div[@class="zuthor"]/text()')
        loader.add_xpath("cover_urls", '//div[@class="cover"]/img/@src')
        loader.add_xpath("state", '//div[@class="state"]/text()')
        loader.add_xpath("desc", '//div[@class="text"]/text()')
        loader.add_value("source", response.url)
        item = loader.load_item()
        # 处理封面链接
        if item["cover_urls"]:
            item["cover_urls"] = [
                i.url for i in response.follow_all(item["cover_urls"])
            ]
        # 返回书籍信息
        return item

    def get_chapter_list(self, response: Response) -> Iterable[str] | None:
        """获取章节列表."""
        yield from response.xpath(
            '//div[@class="chapter container"]/ol/li/a/@href',
        ).getall()

    def get_chapter_info(self, response: Response) -> ChapterItem | None:
        """获取章节信息."""
        # 获取整个 HTML 页面
        html = self.get_html(response)
        if html is None: return None
        loader = ChapterItemLoader(item=ChapterItem(), selector=html)
        loader.add_value("book_hash", response.meta["book_hash"])
        loader.add_value("index", response.meta["index"])
        loader.add_xpath("title", "//h2/text()")
        loader.add_xpath("content", '//article[@id="article"]')
        loader.add_value("source", response.url)
        item = loader.load_item()
        # 记录日志并返回章节信息
        self.logger.debug(
            f"获取到章节信息: {item.get('index', 0)}."
            f"{item.get('title', '未知章节')}",
        )
        return item
