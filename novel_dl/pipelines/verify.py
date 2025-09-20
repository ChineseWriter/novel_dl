#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: verify.py
# @Time: 23/08/2025 20:56
# @Author: Amundsen Severus Rubeus Bjaaland
"""
# verify
验证管道: 用于验证章节下载完整性.
"""

# 导入自定义库: 用于类型注解和判断
from novel_dl.items import ChapterItem


class VerifyPipeline:
    """
    # VerifyPipeline
    验证管道: 用于验证章节下载完整性.
    """
    def __init__(self):
        # 初始化计数器和计数标志
        self.__counter = 0
        self.__flag = False
        
    def open_spider(self, spider):
        """
        # open_spider
        在爬虫启动时调用, 用于初始化计数功能, 
        仅在书籍模式下启用.
        """
        # 如果是书籍模式, 启用计数功能
        if spider.mode == spider.Mode.BOOK:
            self.__flag = True
    
    def process_item(self, item, _):
        """
        # process_item
        处理每个 Item, 如果启用计数功能且当前项是章节, 则计数器加一. 
        最后将 Item 返回给下一个 Pipeline.
        """
        # 如果启用计数功能且当前项是章节, 则计数器加一
        if self.__flag and isinstance(item, ChapterItem):
            self.__counter += 1
        # 将 Item 返回给下一个 Pipeline
        return item
    
    def close_spider(self, spider):
        """
        # close_spider
        在爬虫关闭时调用, 如果启用计数功能且计数器与章节总数不符, 则记录警告日志.
        """
        # 如果启用计数功能且计数器与章节总数不符, 则记录警告日志
        if self.__flag and (self.__counter != spider.chapter_count):
            spider.logger.warning(
                f"书籍未下载完全: {self.__counter}/{spider.chapter_count} 章节!"
            )