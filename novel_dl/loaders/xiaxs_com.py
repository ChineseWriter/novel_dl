#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: xiaxs_com.py
# @Time: 14/07/2025 10:20
# @Author: Amundsen Severus Rubeus Bjaaland


from itemloaders.processors import MapCompose

from novel_dl.utils.str_deal import get_text_after_colon
from novel_dl.utils.str_deal import normalize_book_status

from novel_dl.templates import BookItemLoader as BIL
from novel_dl.templates import ChapterItemLoader as CIL


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
