#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: building.py
# @Time: 11/10/2025 18:42
# @Author: Amundsen Severus Rubeus Bjaaland
"""该模块用于测试项目中的一些代码."""


from pathlib import Path

from novel_dl.utils.importer import TND


if __name__ == "__main__":
    book = TND(Path(__file__).parent / "data/test.epub")
