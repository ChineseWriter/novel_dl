#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: epub.py
# @Time: 25/08/2025 09:48
# @Author: Amundsen Severus Rubeus Bjaaland


import yaml

from ebooklib import epub

from ..entity.base import Book


TEXT_CSS = "text/css"


def get_epub(book: Book):
    ebook = epub.EpubBook()
    
    ebook.set_identifier(book.hash  )
    ebook.set_title(     book.title )
    ebook.add_author(    book.author)
    ebook.set_language(  "zh-CN"    )
    
    ebook.add_metadata("DC", "description", book.desc)
    ebook.add_metadata("DC", "contributor", "Amundsen Severus Rubeus Bjaaland")
    if book.update_time:
        ebook.add_metadata("DC", "date", book.update_time_str)
    
    for i in book.tags:    ebook.add_metadata("DC", "type", i)
    for i in book.sources: ebook.add_metadata("DC", "source", i)
    
    cover = book.main_cover
    if cover is not None:
        cover.to_jpg()
        ebook.set_cover(
            "images/cover.jpg", cover.data
        )
    
    if book.other_info:
        yaml_item = epub.EpubItem(
            uid="other_info",
            file_name="others/other_info.yaml",
            media_type="application/octet-stream",
            content=yaml.dump(book.other_info).encode()
        )
        ebook.add_item(yaml_item)
    
    # 添加章节和简介页面的 CSS 样式
    intro_css = epub.EpubItem(
        uid="introduce_css",
        file_name="styles/introduce.css",
        media_type=TEXT_CSS,
        content=INTRODUCE_CSS.encode()
    )
    ebook.add_item(intro_css)
    chapter_css = epub.EpubItem(
        uid="chapter_css",
        file_name="styles/chapter.css",
        media_type=TEXT_CSS,
        content=CHAPTER_CSS.encode()
    )
    ebook.add_item(chapter_css)
    
    intro_e = epub.EpubHtml(
        uid="introduce_html", lang="zh-CN",
        title=f"《{book.title}》基本信息",
        file_name="pages/intro.xhtml"
    )
    intro_e.add_link(
        rel="stylesheet", type=TEXT_CSS,
        href="../styles/introduce.css"
    )
    intro_e.content = \
f"""
<div class="container">
<div class="cover" >
    <img src="../images/cover.jpg" alt="封面图片" style="width:100%;height:100%;object-fit:cover;">
</div>
<h1>{book.title}</h1>
<p><span class="info-title">作者:&emsp;</span>{book.author}</p>
<p><span class="info-title">描述:&emsp;</span>{book.desc}</p>
<p>
    <span class="info-title">更新时间:&emsp;</span>
    {book.update_time_str if book.update_time else "未知"}
</p>
<p><span class="info-title">标签:&emsp;</span></p>
<ul class="tags">
    {"".join([f"<li>{i}</li>" for i in book.tags])}
</ul>
<p><span class="info-title">来源:</span></p>
<ul class="sources">
    {"".join([f"<li>{i}</li>" for i in book.sources])}
</ul>
</div>"""
    ebook.add_item(intro_e)
    
    ebook.spine = [intro_e, "nav", intro_e]
    toc = []
    
    for chapter in book.chapters:
        # 创建章节页面, 并添加章节的 CSS
        chapter_item = epub.EpubHtml(
            uid=chapter.hash, lang="zh-CN",
            title=f"第{chapter.index}章 {chapter.title}",
            file_name=\
                f"pages/{str(chapter.index).rjust(5, '0')}" \
                f"-{chapter.title}.xhtml",
        )
        chapter_item.add_link(
            rel="stylesheet", type="text/css",
            href="../styles/chapter.css"
        )
        chapter_item.content = \
f"""
<div class="container">
    <h1>第{chapter.index}章&emsp;{chapter.title}</h1>
    <p>
        <span class="info-title">更新时间:&emsp;</span>
        {chapter.update_time_str if chapter.update_time else "未知"}
    </p>
    <div class="chapter-content">
        {
            "".join(
                [
                    f"<p>&emsp;&emsp;{i}</p>"
                    for i in chapter.content.replace("\t", "").split("\n")
                ]
            )
        }
    </div>
    <div class="hidden">
        <h2>来源</h2>
        <ul class="sources">
            {
                "".join(
                    [f"<li>{i}</li>" for i in chapter.sources]
                )
            }
        </ul>
        <div class="other-info">
            <h2>其它信息</h2>
            <dl>
                {
                    "".join(
                        [
                            f"<dt>{k}</dt><dd>{v}</dd>"
                            for k, v in chapter.other_info.items()
                        ]
                    )
                }
            </dl>
        </div>
    </div>
</div>"""
        ebook.add_item(chapter_item)
        toc.append(chapter_item)
        ebook.spine.append(chapter_item)
    
    ebook.toc = toc
    ebook.add_item(epub.EpubNcx())
    ebook.add_item(epub.EpubNav())
    
    return ebook


# 简介页面的 CSS 样式
INTRODUCE_CSS = """body {
    line-height: 1.6;
    margin: 20px;
}
.container {
    max-width: 800px;
    margin: auto;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
h1 {
    color: #333;
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}
p {
    margin: 10px 0;
}
.info-title {
    font-weight: bold;
}
.cover {
    text-align: center;
    margin-bottom: 20px;
}
.cover img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
}
.tags {
    display: flex;
    flex-wrap: wrap;
    list-style-type: none;
    padding: 0;
}
.tags li {
    margin-right: 10px;
}
.sources {
    list-style-type: disc;
    padding-left: 20px;
}"""
# 章节页面的 CSS 样式
CHAPTER_CSS = """body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 20px;
    background-color: #f4f4f4;
}
.container {
    max-width: 800px;
    margin: auto;
    background: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
h1 {
    color: #333;
    border-bottom: 2px solid #333;
    padding-bottom: 10px;
}
p {
    margin: 10px 0;
}
.info-title {
    font-weight: bold;
}
.hidden {
    display: none;
}"""