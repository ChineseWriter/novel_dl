#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: check.py
# @Time: 30/07/2025 11:26
# @Author: Amundsen Severus Rubeus Bjaaland
"""
# CheckPipeline
该管道用于对爬取到的 BookItem 和 ChapterItem 进行有效性和完整性检查,
确保数据符合预期格式和业务逻辑要求.
"""


# 导入第三方库
from scrapy.exceptions import DropItem
# 导入自定义库
from novel_dl.entity.items import BookItem, ChapterItem


class CheckPipeline:
    """
    # CheckPipeline
    该管道用于对爬取到的 BookItem 和 ChapterItem 进行有效性和完整性检查,
    确保数据符合预期格式和业务逻辑要求.

    ## 主要功能
    - 对 BookItem 和 ChapterItem 进行类型判断和字段检查.
    - 检查字段类型、必填字段、默认值、字段间逻辑关系等.
    - 对于不符合要求的 item, 记录警告日志并抛出 DropItem 异常,
        防止错误数据进入后续流程.
    - 对于章节内容过短等非致命问题, 仅记录警告日志, 便于后续排查.

    ## 方法
    - process_item(item, spider): 主入口, 根据 item 类型分发到对应检查方法.
    - check_book_item(item, spider): 检查 BookItem 的
        字段类型、必填项、默认值和逻辑一致性.
    - check_chapter_item(item, spider): 检查 ChapterItem 的
        字段类型、必填项、默认值和逻辑一致性, 并对内容长度进行警告.

    ## 异常处理
    - 检查失败时抛出 AssertionError, 并由 process_item 捕获后抛出 DropItem,
        阻止错误数据流入后续环节.
    """

    # noinspection PyMethodMayBeStatic
    def process_item(self, item, spider):
        """
        # process_item
        对传入的 item 进行类型检查和内容校验.
        根据 item 的类型(BookItem 或 ChapterItem),
        分别调用对应的检查方法(check_book_item 或 check_chapter_item).
        若检查失败, 则记录警告日志并抛出 DropItem 异常丢弃该 item.
        若 item 类型不属于上述两者, 则直接丢弃并记录警告日志.

        ## 参数
        - item: 待处理的 item 实例, 类型为 BookItem 或 ChapterItem.
        - spider: 当前处理 item 的爬虫实例.

        ## 返回值
        校验通过的 item.

        ## 抛出异常说明
        - DropItem: 当 item 校验失败或类型不正确时抛出.
        """
        # 判断 Item 的类型, 并依据类型进行处理
        if isinstance(item, BookItem):
            # 若为 BookItem 类型则执行 check_book_item 检查
            try:
                CheckPipeline.check_book_item(item, spider)
            except AssertionError as error:
                spider.logger.warning(
                    f"BookItem 检查失败: \n'{repr(item)}' -> {str(error)}"
                )
                raise DropItem(str(error)) from error
            spider.logger.debug(f"BookItem 检查通过: '{repr(item)}'")
            return item
        if isinstance(item, ChapterItem):
            # 若为 ChapterItem 类型则执行 check_chapter_item 检查
            try:
                CheckPipeline.check_chapter_item(item, spider)
            except AssertionError as error:
                spider.logger.warning(
                    f"ChapterItem 检查失败: \n'{repr(item)}' -> {str(error)}"
                )
                raise DropItem(str(error)) from error
            spider.logger.debug(f"ChapterItem 检查通过: '{repr(item)}'")
            return item
        # 若二者都不是则 Item 类型存在错误, 丢弃该 Item
        spider.logger.warning(
            f"Item 检查失败: '{repr(item)}' "
            "不是一个 BookItem 或 ChapterItem."
        )
        raise DropItem(
            f"'{repr(item)}' 不是一个 BookItem 或 ChapterItem."
        )

    @staticmethod
    def check_book_item(item, _):
        """
        # check_book_item
        检查 BookItem 的有效性和完整性.

        ## 参数
        - item: BookItem 实例, 需要检查的书籍信息.
        - _: 爬虫实例, 可用于记录日志或其他操作.

        ## 检查内容
        - 必填字段检查, 确保必要字段不为空.
        - 转换可能为空的字段为默认值.
        - 类型检查, 确保字段类型正确.
        - 非默认值检查, 确保部分字段不使用默认值.
        - 逻辑检查, 确保封面 URL 列表和封面图片列表一致.
        - 其他逻辑检查, 确保数据的一致性和完整性.

        ## 抛出异常说明：
        - 如果检查失败, 抛出 AssertionError 异常.
        """
        # 必填字段检查
        assert "title"  in item, "书籍标题不能为空"
        assert "author" in item, "书籍作者不能为空"
        assert "state"  in item, "书籍状态不能为空"
        assert "desc"   in item, "书籍简介不能为空"
        assert "source" in item, "书籍来源不能为空"

        # 转换可能为空的字段
        if "other_info" not in item: item["other_info"] = {}
        if "cover_urls" not in item: item["cover_urls"] = []
        if "covers"     not in item: item["covers"]     = []

        # 类型检查
        assert isinstance(item["title"],      str),  "书籍标题不是字符串"
        assert isinstance(item["author"],     str),  "书籍作者不是字符串"
        assert isinstance(item["state"],      str),  "书籍状态不是字符串"
        assert isinstance(item["desc"],       str),  "书籍简介不是字符串"
        assert isinstance(item["source"],     str),  "书籍来源不是字符串"
        assert isinstance(item["other_info"], dict), "书籍其它信息不是字典"
        assert isinstance(item["cover_urls"], list), \
            "书籍封面 URL 列表属性不是列表"
        assert isinstance(item["covers"],     list), \
            "书籍封面图片列表属性不是列表"
        for i in item["cover_urls"]:
            assert isinstance(i, str), \
                "书籍封面 URL 列表中的元素不是字符串"
        for i in item["covers"]:
            assert isinstance(i, dict), \
                "书籍封面图片列表中的元素不是字典"

        # 非默认值检查
        assert item["title"]  != "默认书籍名",  "书籍标题不能是默认值"
        assert item["author"] != "默认作者",    "书籍作者不能是默认值"
        assert item["desc"]   != "默认书籍简介", "书籍简介不能是默认值"
        assert item["source"] != "https://example.com", \
            "书籍来源不能是默认 URL"

        # 逻辑检查
        assert len(item["cover_urls"]) == len(item["covers"]), \
            "书籍封面 URL 列表和封面图片列表长度不一致"
        assert item["state"] in ["完结", "连载", "断更", "未知"], \
            "书籍状态只能是'完结'、'连载'、'断更'、'未知'中的一种"

    @staticmethod
    def check_chapter_item(item, spider):
        """
        # check_chapter_item
        检查 ChapterItem 的有效性和完整性.

        ## 参数
        - item: ChapterItem 实例, 需要检查的章节信息.
        - spider: 爬虫实例, 可用于记录日志或其他操作.

        ## 检查内容
        - 必填字段检查, 确保必要字段不为空.
        - 转换可能为空的字段为默认值.
        - 类型检查, 确保字段类型正确.
        - 非默认值检查, 确保字段不使用默认值.
        - 逻辑检查, 确保章节索引和更新时间的合理性.
        - 其它检查, 确保章节内容的完整性, 该检查不抛出异常, 仅记录警告.

        ## 抛出异常
        - 如果检查失败, 抛出 AssertionError 异常.
        """
        # 必填字段检查
        assert "book_hash" in item, "章节所属书籍的哈希值不能为空"
        assert "index"     in item, "章节索引不能为空"
        assert "title"     in item, "章节标题不能为空"
        assert "content"   in item, "章节内容不能为空"
        assert "source"    in item, "章节来源不能为空"

        # 转换可能为空的字段
        if "update_time" not in item: item["update_time"] = 0.0
        if "other_info"  not in item: item["other_info"]  = {}

        # 类型检查
        assert isinstance(item["book_hash"],   str), \
            "章节所属书籍的哈希值不是字符串"
        assert isinstance(item["index"],       int), "章节索引不是整数"
        assert isinstance(item["title"],       str), "章节标题不是字符串"
        assert isinstance(item["content"],     str), "章节内容不是字符串"
        assert isinstance(item["source"],      str), "章节来源不是字符串"
        assert isinstance(item["update_time"], float), \
            "章节更新时间不是浮点数"
        assert isinstance(item["other_info"],  dict), \
            "章节其它信息不是字典"

        # 非默认值检查
        assert item["title"]   != "默认章节名",  "章节标题不能是默认值"
        assert item["content"] != "默认章节内容", "章节内容不能是默认值"
        assert item["source"]  != "https://example.com", \
            "章节来源不能是默认 URL"

        # 逻辑检查
        assert len(item["book_hash"]) == 64,  "书籍哈希字符值必须为 64 位"
        assert item["index"]          >= 0,   "章节索引不能为负数"
        assert item["update_time"]    >= 0.0, "章节更新时间不能为负数"

        # 其它检查
        if len(item["content"]) <= 800:
            spider.logger.warning(
                f"章节 '{item["title"]}' 的内容过短, 可能是抓取不完整: \n"
                f"{item["content"]}"
            )
