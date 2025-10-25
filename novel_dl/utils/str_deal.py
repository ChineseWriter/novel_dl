#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: str_deal.py
# @Time: 14/07/2025 11:15
# @Author: Amundsen Severus Rubeus Bjaaland
"""该模块包含一些字符串处理的实用函数."""


END = ["已完结", "完结", "完本"]
SERIALIZING = ["连载", "连载中"]
BREAK = ["断更"]


def get_text_after_colon(text: str) -> str:
    """获取冒号后面的文本."""
    if "：" in text:                 # noqa: RUF001
        return text.split("：")[-1]  # noqa: RUF001
    if ":" in text:
        return text.split(":")[-1]
    return text


def get_text_after_space(text: str) -> str:
    """获取第一个空格后面的文本."""
    if " " in text:
        return " ".join(text.split(" ")[1:])
    return text


def normalize_book_status(status: str) -> str:
    """规范化书籍状态文本."""
    if status in END:         return "完结"
    if status in SERIALIZING: return "连载"
    if status in BREAK:       return "断更"
    return "未知"


def add_tab(text: str) -> str:
    """若行首没有制表符, 则添加制表符缩进."""
    # 按行分割文本.
    text_list = text.split("\n")
    # 处理每一行.
    buffer = []
    for i in text_list:
        # 去除行首尾的空白字符.
        line = i.strip()
        # 仅处理非空行.
        if line:
            # 若行首没有制表符, 则添加一个.
            if not line.startswith("\t"):
                line = "\t" + line
            # 将处理后的行添加到缓冲区.
            buffer.append(line)
    # 将缓冲区的行重新连接成一个字符串并返回.
    return "\n".join(buffer)
