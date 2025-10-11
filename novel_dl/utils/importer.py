#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: importer.py
# @Time: 11/10/2025 18:38
# @Author: Amundsen Severus Rubeus Bjaaland
"""用于将其他项目下载的小说以兼容的方式导入至该项目中.

支持导入的项目如下:

1. [Tomato-Novel-Downloader](https://github.com/zhongbai2333/Tomato-Novel-Downloader)
"""


from pathlib import Path

from bs4 import BeautifulSoup as bs
from ebooklib import epub

from novel_dl.entity.base import Book, Chapter, Cover
from novel_dl.utils.identify import hash_
from novel_dl.utils.str_deal import normalize_book_status


def TND(path: Path) -> Book:
    if not path.exists():
        raise FileNotFoundError(f"文件 {path} 不存在.")
    if path.suffix.lower() != ".epub":
        raise ValueError(f"文件 {path} 不是 epub 格式.")

    book: epub.EpubBook = epub.read_epub(str(path))  # type: ignore[reportUnknownVariableType]
    intro = book.get_item_with_href("intro.xhtml")  # type: ignore[reportUnknownVariableType]
    cover = book.get_item_with_href("cover.jpg")  # type: ignore[reportUnknownVariableType]
    intro_page = bs(intro.get_content(), "lxml")
    title = intro_page.find("h2")
    if title is None:
        raise ValueError("无法从电子书中提取书籍标题.")
    title = title.text
    info_fields = intro_page.find_all("p", attrs={"class": "no-indent"})
    author = info_fields[0].text.split("：")[-1]  # noqa: RUF001
    state = info_fields[1].text.split("；")[0].split("：")[-1]  # noqa: RUF001
    state = normalize_book_status(state)
    desc = str(intro_page.find_all("p")[-1])[3:-4].replace("<br/>", "\n")
    book_obj = Book(title, author, state, desc, [], [], {})  # type: ignore[reportUnknownVariableType]
    book_obj.covers.append(Cover("", cover.get_content()))

    spine = book.spine  # type: ignore[reportUnknownVariableType]
    item_list = [book.get_item_with_id(i[0]) for i in spine][1:]
    for index, item in enumerate(item_list):
        content = bs(item.get_content(), "lxml")
        book_obj.append(
            Chapter(
                hash_(book), index + 1, content.find("h1").text, 0.0,
                "\t" + "\n\t".join(i.text for i in content.find_all("p")),
                [], {},
            ),
        )
    return book_obj
