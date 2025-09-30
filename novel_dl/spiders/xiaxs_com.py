#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: xiaxs_com.py
# @Time: 30/06/2025 18:43
# @Author: Amundsen Severus Rubeus Bjaaland


import re
from collections.abc import Iterable

from itemloaders.processors import MapCompose
from scrapy.http import Request, Response

from novel_dl.items import BookItem, ChapterItem
from novel_dl.loaders.xiaxs_com import BookItemLoader, ChapterItemLoader
from novel_dl.templates import BookItemLoader as BIL
from novel_dl.templates import ChapterItemLoader as CIL
from novel_dl.templates import GeneralSpider
from novel_dl.utils.str_deal import get_text_after_colon, normalize_book_status


def deal_content(content: str) -> str:
    try:
        data = content[34:-6].replace("\u3000", "")
        paras = data.split("<br>")
        paras = list(filter(lambda x: True if x else False, paras))[:-1]
        para_buffer = []
        for para in paras:
            words = para.split("</i>")[:-1]
            words_buffer = ""
            for word in words:
                word = word.split("\"")[-2]
                word = word.split("-")[-1]
                words_buffer += chr(int(word, 16))
            words_buffer = words_buffer.split("网站公告")[0]
            words_buffer = words_buffer.split("爱读免费小说")[0]
            para_buffer.append(words_buffer.strip())
        data = "\t" + "\n\t".join(para_buffer)
        return data
    except Exception:
        return "默认章节内容"


class BookItemLoader(BIL):
    state_in       = MapCompose(
        str.strip,
        get_text_after_colon,
        normalize_book_status
    )


class ChapterItemLoader(CIL):
    title_in       = MapCompose(
        str.strip,
        lambda x: x.split("-")[0],
        lambda x: x.split(" ")[-1]
    )
    content_in     = MapCompose(str.strip, deal_content)


class XiaxsSpider(GeneralSpider):
    name = "xiaxs_com"
    domain = "www.xiaxs.com"
    book_url_pattern = re.compile(r"^/xs/\d+\/$")
    chapter_url_pattern = re.compile(r"^/xs/\d+/\d+\.html$")
    
    custom_settings = {
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 403, 404, 523, 520]
    }
    
    def get_book_info(self, response: Response) -> BookItem | None:
        html = response.xpath("/*")
        if len(html) != 1:
            self.logger.error("在该次请求中没有找到 HTML 元素")
            return None
        
        loader = BookItemLoader(
            item=BookItem(), selector=html[0]
        )
        loader.add_xpath("title", "//h1/text()")
        loader.add_xpath(
            "author",
            "/html/body/div[4]/div[1]/div[2]/div[2]/p[1]/a/text()"
        )
        loader.add_xpath(
            "cover_urls",
            "/html/body/div[4]/div[1]/div[2]/div[1]/img/@src"
        )
        loader.add_xpath(
            "state",
            "/html/body/div[4]/div[1]/div[2]/div[2]/p[2]/text()"
        )
        loader.add_xpath("desc", '//*[@id="intro"]/text()')
        loader.add_value("source", response.url)
        item = loader.load_item()
        
        if item["cover_urls"]:
            item["cover_urls"] = \
                [
                    i.url for i in
                    response.follow_all(item["cover_urls"])
                ]
        return item
    
    def get_chapter_list(
        self, response: Response, book: BookItem
    ) -> Iterable[Request] | None:
        href_list = response.xpath(
            '//div[@class="listmain"]/dl/dt[2]'
            '/following-sibling::dd/a/@href'
        ).getall()
        
        for index, url in enumerate(href_list):
            yield response.follow(
                url, self.get_chapter_info,
                meta={
                    "index": index + 1,
                    "book_hash": book.book_hash
                }
            )
    
    def get_chapter_info(
        self, response: Response
    ) -> ChapterItem | None:
        html = response.xpath("/*")
        if len(html) != 1:
            self.logger.error("在该次请求中没有找到 HTML 元素")
            return None
        
        loader = ChapterItemLoader(
            item=ChapterItem(), selector=html[0]
        )
        loader.add_value("book_hash", response.meta["book_hash"])
        loader.add_value("index", response.meta["index"])
        loader.add_xpath("title", "/html/head/title/text()")
        loader.add_xpath("content", '//*[@id="content"]')
        loader.add_value("source", response.url)
        item = loader.load_item()
        
        self.logger.debug(
            f"获取到章节信息：{item.get('index', 0)}."
            f"{item.get('title', '未知章节')}"
        )
        return item
        
