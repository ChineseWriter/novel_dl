#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: importer.py
# @Time: 11/10/2025 18:38
# @Author: Amundsen Severus Rubeus Bjaaland
"""用于将其他项目下载的小说以兼容的方式导入至该项目中.

支持导入的项目如下:

1. [Tomato-Novel-Downloader](https://github.com/zhongbai2333/Tomato-Novel-Downloader)
"""

# 导入标准库
from pathlib import Path

# 导入第三方库
from bs4 import BeautifulSoup as bs
from ebooklib import epub  # type: ignore[reportMissingTypeStubs]

# 导入自定义库
from novel_dl.entity.base import Book, Chapter, Cover
from novel_dl.utils.identify import hash_
from novel_dl.utils.str_deal import normalize_book_status


def tnd(path: Path) -> Book:
    """从 Tomato-Novel-Downloader 导出的 epub 文件中导入小说."""
    # 检查文件是否存在
    if not path.exists(): raise FileNotFoundError(f"文件 {path} 不存在.")
    # 简单检查文件格式
    if path.suffix.lower() != ".epub":
        raise ValueError(f"文件 {path} 不是 epub 格式.")
    # 读取 epub 文件
    book: epub.EpubBook = epub.read_epub(str(path))
    # 获取简介页面和封面图片
    intro = book.get_item_with_href("intro.xhtml")  # type: ignore[reportUnknownVariableType]
    cover = book.get_item_with_href("cover.jpg")  # type: ignore[reportUnknownVariableType]
    # 检查是否成功获取
    if not isinstance(intro, epub.EpubHtml):
        raise ValueError("无法从电子书中提取简介页面.")
    if not isinstance(cover, epub.EpubItem):
        raise ValueError("无法从电子书中提取封面图片.")
    # 解析简介页面为 bs 对象
    intro_page = bs(intro.get_content(), "xml")
    # 提取书籍的标题
    title = intro_page.find("h2")
    if title is None: raise ValueError("无法从电子书中提取书籍标题.")
    title = title.text
    # 提取含有书籍信息的字段
    info_fields = intro_page.find_all("p", attrs={"class": "no-indent"})
    # 获取作者信息
    author = info_fields[0].text.split("：")[-1]  # noqa: RUF001
    # 获取书籍状态
    state = info_fields[1].text.split("；")[0].split("：")[-1]  # noqa: RUF001
    state = normalize_book_status(state)
    # 获取书籍简介
    desc = str(intro_page.find_all("p")[-1])[3:-4].replace(
        "<br/>", "\n",
    ).replace("\n\n", "\n").replace("\n\n", "\n")
    # 构造 Book 对象
    book_obj = Book(title, author, state, desc, [], [], {})  # type: ignore[reportUnknownVariableType]
    # 向 Book 对象中添加封面
    book_obj.covers.append(Cover("", cover.get_content()))
    # 获取章节的 id 列表
    spine: list[tuple[str, str]] = book.spine
    # 初始化章节对象列表
    item_list: list[epub.EpubHtml] = []
    # 遍历章节 id 列表
    for i in spine[1:]:
        # 依据 id 获取章节对象
        item = book.get_item_with_id(i[0])  # type: ignore[reportUnknownVariableType]
        # 确保章节对象类型正确
        if isinstance(item, epub.EpubHtml):
            item_list.append(item)
    # 解析章节内容并添加至 Book 对象中
    for index, item in enumerate(item_list):
        # 解析章节内容为 bs 对象
        content = bs(item.get_content(), "xml")
        # 提取章节标题
        name = content.find("h1")
        if name is None: continue
        name = " ".join(name.text.split(" ")[1:])
        # 提取章节正文内容并添加至 Book 对象中
        book_obj.append(
            Chapter(
                hash_(book_obj), index + 1, name, 0.0,
                "\t" + "\n\t".join(i.text for i in content.find_all("p")),
                [], {},
            ),
        )
    # 返回构造完成的 Book 对象
    return book_obj

IMPORTERS = {
    "tnd": tnd,
}
