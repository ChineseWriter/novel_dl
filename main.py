#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: main.py
# @Time: 12/10/2025 13:26
# @Author: Amundsen Severus Rubeus Bjaaland
"""项目的主入口, 用于启动爬虫和管理爬虫任务."""

# 导入标准库
from pathlib import Path

# 导入第三方库
import fire
from ebooklib import epub

# 导入自定义库
from novel_dl.settings import DATA_DIR
from novel_dl.utils.db_manager import DBManager
from novel_dl.utils.epub import get_epub
from novel_dl.utils.importer import IMPORTERS


class Main:
    """项目的主入口, 用于启动爬虫和管理爬虫任务."""

    def import_(self, path: str | Path, func: str) -> None:
        """导入数据的命令行接口."""
        # 规范化路径
        path = path if isinstance(path, Path) else Path(path)
        # 检查文件是否存在
        if not path.exists():
            print(f"文件 {path} 不存在.")
            return
        # 检查导入方法是否支持
        if func not in IMPORTERS:
            print(f"不支持的导入方法: {func}.")
            return
        # 尝试创建 Book 对象
        try: book = IMPORTERS[func](path)
        except Exception as e:  # noqa: BLE001
            print(f"导入失败: {e}.")
            return
        # 将 Book 对象添加至数据库
        DBManager().add_book(book)
        print(f"成功导入书籍: {book.title}.")

    def export(self) -> None:
        """导出数据的命令行接口."""
        # 创建导出目录
        output_dir = DATA_DIR / "export"
        # 确保导出目录存在
        if not output_dir.exists(): output_dir.mkdir(parents=True, exist_ok=True)
        # 获取用户输入的书籍名称
        name = input("请输入要导出的书籍名称: ").strip()
        # 根据输入获取书籍列表
        book_list = DBManager().search_book_by_name(name)
        # 检查是否找到书籍
        if len(book_list) == 0:
            print(f"未找到书籍: {name}.")
            return
        # 列出找到的书籍
        print(f"找到 {len(book_list)} 本书籍:")
        for index, book_obj in enumerate(book_list):
            print(f"{index + 1}. {book_obj.title} - {book_obj.author}")
        # 获取用户选择的书籍索引
        choice = input("请输入要导出的书籍索引: ").strip()
        # 将用户输入转换为索引
        try: choice_index = int(choice)
        except ValueError:
            print("无效的索引输入.")
            return
        else:
            # 检查索引范围
            if choice_index < 1 or choice_index > len(book_list):
                print("索引超出范围.")
                return
            # 导出选中的书籍
            book_obj = book_list[choice_index - 1]
            book = get_epub(book_obj)
            book_path = output_dir / f"{book_obj.author}-{book_obj.title}.epub"
            epub.write_epub(str(book_path), book, {})
            print(f"成功导出: {book_obj.title}.")


if __name__ == "__main__":
    fire.Fire(Main)
