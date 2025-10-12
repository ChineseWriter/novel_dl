#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: __init__.py
# @Time: 06/10/2025 08:33
# @Author: Amundsen Severus Rubeus Bjaaland
"""novel_dl 包的初始化文件."""

# 导入标准库
from pathlib import Path


MEDIA_DIR = Path(__file__).parent / "media"

__version__: dict[str, list[str]] = {
    "0.1.0": ["初始化项目."],
    "0.1.1": ["增加对番茄小说网的支持, 注意, 不支持下载小说具体内容."],
}
