#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: str_deal.py
# @Time: 14/07/2025 11:15
# @Author: Amundsen Severus Rubeus Bjaaland


import hashlib


END = ["已完结", "完结", "完本"]
SERIALIZING = ["连载", "连载中"]
BREAK = ["断更"]


def get_text_after_colon(text: str) -> str:
    """
    获取冒号后面的文本
    
    :param text: 输入文本
    :return: 冒号后面的文本，如果没有冒号则返回原文本
    """
    if "：" in text:
        return text.split("：")[-1]
    return text


def normalize_book_status(status: str) -> str:
    """
    规范化书籍状态文本
    
    :param status: 原始状态文本
    :return: 规范化后的状态文本
    """
    if   status in END:         return "完结"
    elif status in SERIALIZING: return "连载"
    elif status in BREAK:       return "断更"
    else:                       return "未知"


def add_tab(text: str) -> str:
    """
    若行首没有制表符, 则添加制表符缩进
    
    :param text: 输入文本
    :return: 添加制表符缩进后的文本
    """
    text_list = text.split("\n")
    buffer = []
    for i in text_list:
        line = i.strip()
        if line:
            if not line.startswith("\t"):
                line = "\t" + line
            buffer.append(line)
    return "\n".join(buffer)