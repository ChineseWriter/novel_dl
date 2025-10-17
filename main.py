#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: main.py
# @Time: 12/10/2025 13:26
# @Author: Amundsen Severus Rubeus Bjaaland
"""项目的主入口, 用于启动爬虫和管理爬虫任务."""

from pathlib import Path

import fire
from ebooklib import epub

from novel_dl.settings import DATA_DIR
from novel_dl.utils.db_manager import DBManager
from novel_dl.utils.epub import get_epub
from novel_dl.utils.importer import tnd


class Main:
    """项目的主入口, 用于启动爬虫和管理爬虫任务."""

    def import_(self, path: str | Path) -> None:
        """导入数据的命令行接口."""
        path = path if isinstance(path, Path) else Path(path)
        if not path.exists():
            print(f"文件 {path} 不存在.")
        book = tnd(path)
        db_manager = DBManager()
        db_manager.add_book(book)
        print(f"成功导入书籍: {book.title}.")

    def export(self, name: str) -> None:
        """导出数据的命令行接口."""
        output_dir = DATA_DIR / "export"
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        db_manager = DBManager()
        book_list = db_manager.search_book_by_name(name)
        if len(book_list) == 0:
            print(f"未找到书籍: {name}.")
            return
        for book_obj in book_list:
            book = get_epub(book_obj)
            epub.write_epub(str(output_dir / f"{book_obj.author}-{book_obj.title}.epub"), book, {})
            print(f"成功导出: {book_obj.title}.")


if __name__ == "__main__":
    fire.Fire(Main)
