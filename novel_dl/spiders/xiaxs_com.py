#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: xiaxs_com.py
# @Time: 30/06/2025 18:43
# @Author: Amundsen Severus Rubeus Bjaaland
"""xiaxs.com 小说爬虫."""


# 导入标准库
import re
from collections.abc import Iterable

# 导入第三方库
from itemloaders.processors import MapCompose
from scrapy.http import Response

# 导入自定义库
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import BookItemLoader as BIL
from novel_dl.templates import ChapterItemLoader as CIL
from novel_dl.templates import GeneralSpider
from novel_dl.utils.str_deal import get_text_after_colon, normalize_book_status


def deal_content(content: str) -> str | None:
    """处理章节内容."""
    # 确保内容长度, 防止出现 index out of range 错误
    if len(content) < 40: return None
    # 除去 div 标签
    data = content[34:-6]
    # 除去特殊字符
    data = data.replace("\u3000", "")
    # 按照 <br> 分割段落
    paras = data.split("<br>")
    # 除去空段落
    paras = list(filter(lambda x: bool(x), paras))
    # 除去最后一个段落(通常是广告)
    paras = paras[:-1]
    # 处理每个段落
    para_buffer: list[str] = []
    for para in paras:
        # 按照 </i> 分割每个字
        words = para.split("</i>")[:-1]
        # 处理每个字
        words_buffer = ""
        for one_word in words:
            # 提取十六进制编码
            word = one_word.split('"')[-2]
            word = word.split("-")[-1]
            # 转换为字符, 默认该编码为 Unicode 编码
            words_buffer += chr(int(word, 16))
        # 除去网站公告和内容水印
        words_buffer = words_buffer.split("网站公告")[0]
        words_buffer = words_buffer.split("爱读免费小说")[0]
        # 加入段落列表
        para_buffer.append(words_buffer.strip())
    # 合并为字符串, 添加制表符和换行符, 返回
    return "\t" + "\n\t".join(para_buffer)


class BookItemLoader(BIL):
    """书籍信息数据加载器."""

    state_in       = MapCompose(
        str.strip,
        get_text_after_colon,
        normalize_book_status,
    )


class ChapterItemLoader(CIL):
    """章节信息数据加载器."""

    title_in       = MapCompose(
        str.strip,
        lambda x: x.split("-")[0],
        lambda x: x.split(" ")[-1],
        lambda x: "、".join(x.split("、")[1:]) if "章、" in x else x,
    )
    content_in     = MapCompose(str.strip, deal_content)


class XiaxsSpider(GeneralSpider):
    """xiaxs.com 小说爬虫."""

    name = "xiaxs_com"
    domain = "www.xiaxs.com"
    book_url_pattern = re.compile(r"^/xs/\d+\/$")
    chapter_url_pattern = re.compile(r"^/xs/\d+/\d+\.html$")

    custom_settings = {
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 403, 404, 523, 520],
    }

    def get_book_info(self, response: Response) -> BookItem | None:
        """获取书籍信息."""
        # 获取整个 HTML 页面
        html = self.get_html(response)
        if html is None: return None
        # 使用 ItemLoader 提取书籍信息
        loader = BookItemLoader(item=BookItem(), selector=html)
        loader.add_xpath("title", "//h1/text()")
        loader.add_xpath("author", "/html/body/div[4]/div[1]/div[2]/div[2]/p[1]/a/text()")
        loader.add_xpath("cover_urls", "/html/body/div[4]/div[1]/div[2]/div[1]/img/@src")
        loader.add_xpath("state", "/html/body/div[4]/div[1]/div[2]/div[2]/p[2]/text()")
        loader.add_xpath("desc", '//*[@id="intro"]/text()')
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
            '//div[@class="listmain"]/dl/dt[2]'
            '/following-sibling::dd/a/@href',
        ).getall()

    def get_chapter_info(self, response: Response) -> ChapterItem | None:
        """获取章节信息."""
        # 获取整个 HTML 页面
        html = self.get_html(response)
        if html is None: return None
        # 使用 ItemLoader 提取章节信息
        loader = ChapterItemLoader(item=ChapterItem(), selector=html)
        loader.add_value("book_hash", response.meta["book_hash"])
        loader.add_value("index", response.meta["index"])
        loader.add_xpath("title", "/html/head/title/text()")
        loader.add_xpath("content", '//*[@id="content"]')
        loader.add_value("source", response.url)
        item = loader.load_item()
        # 记录日志并返回章节信息
        self.logger.debug(
            f"获取到章节信息: {item.get('index', 0)}."
            f"{item.get('title', '未知章节')}",
        )
        return item

