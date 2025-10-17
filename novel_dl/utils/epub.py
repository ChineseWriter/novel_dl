#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: epub.py
# @Time: 25/08/2025 09:48
# @Author: Amundsen Severus Rubeus Bjaaland
"""将 Book 对象转换为 epub 格式的电子书."""


# 导入标准库
import yaml
from ebooklib import epub  # type: ignore[reportMissingTypeStubs]

# 导入自定义库
from novel_dl import MEDIA_DIR
from novel_dl.entity.base import Book, Chapter
from novel_dl.utils.identify import hash_


# CSS 标记
TEXT_CSS = "text/css"
# 取出模板文件内容
with (MEDIA_DIR / "css" / "intro.css"    ).open("r", encoding="UTF-8") as f:
    INTRODUCE_CSS = f.read()
with (MEDIA_DIR / "css" / "chapter.css"  ).open("r", encoding="UTF-8") as f:
    CHAPTER_CSS = f.read()
with (MEDIA_DIR / "html" / "intro.html"  ).open("r", encoding="UTF-8") as f:
    INTRODUCE_HTML = f.read()
with (MEDIA_DIR / "html" / "chapter.html").open("r", encoding="UTF-8") as f:
    CHAPTER_HTML = f.read()

def _get_intro_html(book: Book) -> str:
    """生成电子书的简介页面."""
    content = INTRODUCE_HTML.replace("{{ title }}",           book.title          )
    content = content.replace(       "{{ author }}",          book.author         )
    content = content.replace(       "{{ update_time_str }}", book.update_time_str)
    content = content.replace(
        "{{ desc }}",
        "".join(
            f"<p>&emsp;&emsp;{i}</p>"
            for i in book.desc.replace("\t", "").split("\n")
        ),
    )
    content = content.replace(
        "{{ tags }}",
        (
            "".join(f'<span class="tag">{i}</span>' for i in book.tags)
            if bool(book.tags) else "<span>None</span>"
        ),
    )
    content = content.replace(
        "{{ sources }}",
        "".join(f'<li><a href="{i}">{i}</a></li>' for i in book.sources),
    )
    return content  # noqa: RET504

def _get_chapter_html(chapter: Chapter) -> str:
    """生成电子书的章节页面."""
    content = CHAPTER_HTML.replace("{{ index }}",           str(chapter.index)     )
    content = content.replace(     "{{ title }}",           chapter.title          )
    content = content.replace(     "{{ update_time_str }}", chapter.update_time_str)
    content = content.replace(
        "{{ content }}",
        "".join(
            f"<p>&emsp;&emsp;{i}</p>"
            for i in chapter.content.replace("\t", "").split("\n")
        ),
    )
    content = content.replace(
        "{{ source }}",
        "".join(f"<li><a href='{i}'>{i}</a></li>" for i in chapter.sources),
    )
    content = content.replace(
        "{{ other_info }}",
        "".join(
            f"<dt>{k}</dt><dd>{v}</dd>"
            for k, v in chapter.other_info.items()
        ),
    )
    return content  # noqa: RET504

def get_epub(book: Book) -> epub.EpubBook:
    """将 Book 对象转换为 epub 格式的电子书."""
    # 创建电子书对象
    ebook = epub.EpubBook()
    # 设置电子书的基本元数据
    ebook.set_identifier(hash_(book))
    ebook.set_title(     book.title )
    ebook.add_author(    book.author)
    ebook.set_language(  "zh-CN"    )
    # 设置电子书的其他元数据
    ebook.add_metadata("DC", "description", book.desc)
    ebook.add_metadata("DC", "contributor", "Amundsen Severus Rubeus Bjaaland")
    if book.update_time: ebook.add_metadata("DC", "date", book.update_time_str)
    for i in book.tags:    ebook.add_metadata("DC", "type", i)
    for i in book.sources: ebook.add_metadata("DC", "source", i)
    # 添加封面
    cover = book.main_cover
    if cover is not None:
        ebook.set_cover("images/cover.jpg", cover.to_jpg().data)
    # 添加其他信息的 YAML 文件
    if book.other_info:
        ebook.add_item(
            epub.EpubItem(
                uid="other_info",
                file_name="others/other_info.yaml",
                media_type="application/octet-stream",
                content=yaml.dump(book.other_info).encode(),
            ),
        )
    # 添加章节和简介页面的 CSS 样式
    intro_css = epub.EpubItem(
        uid="introduce_css",
        file_name="styles/introduce.css",
        media_type=TEXT_CSS,
        content=INTRODUCE_CSS.encode(),
    )
    ebook.add_item(intro_css)
    chapter_css = epub.EpubItem(
        uid="chapter_css",
        file_name="styles/chapter.css",
        media_type=TEXT_CSS,
        content=CHAPTER_CSS.encode(),
    )
    ebook.add_item(chapter_css)
    # 创建简介页面
    intro_e = epub.EpubHtml(
        uid="introduce_html", lang="zh-CN",
        title=f"《{book.title}》基本信息",
        file_name="pages/intro.xhtml",
    )
    intro_e.content = _get_intro_html(book)
    intro_e.add_link(
        rel="stylesheet", type=TEXT_CSS,
        href="../styles/introduce.css",
    )
    ebook.add_item(intro_e)
    # 创建目录
    spine: list[epub.EpubHtml | str] = [intro_e]
    toc_buffer = []
    # 处理每一章节
    for chapter in book.chapters:
        # 创建章节页面, 并添加章节的 CSS
        file_name = (
            f"pages/{str(chapter.index).rjust(5, '0')}"
            f"-{chapter.title}.xhtml"
        )
        title = f"第{chapter.index}章 {chapter.title}"
        chapter_hash = hash_(chapter)
        chapter_item = epub.EpubHtml(
            uid=chapter_hash, lang="zh-CN",
            title=title,
            file_name=file_name,
        )
        chapter_item.add_link(
            rel="stylesheet", type="text/css",
            href="../styles/chapter.css",
        )
        chapter_item.content = _get_chapter_html(chapter)
        ebook.add_item(chapter_item)
        # 将章节添加到目录中
        toc_buffer.append(chapter_item)
        spine.append(chapter_item)
    # 合成目录
    ebook.toc = (
        epub.Link("pages/intro.xhtml", "书封页", "0"*64),
        (epub.Section("小说章节"), tuple(toc_buffer)),
    )
    ebook.spine = spine
    # 添加导航文件
    ebook.add_item(epub.EpubNcx())
    ebook.add_item(epub.EpubNav())
    # 返回电子书对象
    return ebook
