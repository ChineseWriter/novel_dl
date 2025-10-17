#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: check.py
# @Time: 30/07/2025 11:26
# @Author: Amundsen Severus Rubeus Bjaaland
"""数据检查管道模块.

该管道用于对爬取到的 BookItem 和 ChapterItem 进行有效性和完整性检查,
确保数据符合预期格式和业务逻辑要求.
"""


# 导入标准库
from typing import Any

# 导入第三方库
from scrapy.exceptions import DropItem

# 导入自定义库
from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import GeneralSpider


# 默认的源 URL.
DEFAULT_URL = "https://www.example.com/"


class CheckPipeline:
    """数据检查管道.

    该管道用于对爬取到的 BookItem 和 ChapterItem 进行有效性和完整性检查,
    确保数据符合预期格式和业务逻辑要求.
    """

    # noinspection PyMethodMayBeStatic
    def process_item(
            self, item: Any, spider: GeneralSpider,
        ) -> BookItem | ChapterItem:
        """主要的处理方法.

        对传入的 item 进行类型检查和内容校验.
        根据 item 的类型(BookItem 或 ChapterItem),
        分别调用对应的检查方法(check_book_item 或 check_chapter_item).
        若检查失败, 则记录警告日志并抛出 DropItem 异常丢弃该 item.
        若 item 类型不属于上述两者, 则直接丢弃并记录警告日志.
        """
        # 判断 Item 的类型, 并依据类型进行处理
        if isinstance(item, BookItem):
            # 若为 BookItem 类型则执行 check_book_item 检查
            try: passed_item = CheckPipeline.check_book_item(item, spider)
            except AssertionError as error:
                spider.logger.warning(
                    f"BookItem 检查失败: \n'{item!r}' -> {error}",
                )
                raise DropItem(str(error)) from error
            spider.logger.debug(f"BookItem 检查通过: '{item!r}'")
            return passed_item
        if isinstance(item, ChapterItem):
            # 若为 ChapterItem 类型则执行 check_chapter_item 检查
            try: CheckPipeline.check_chapter_item(item, spider)
            except AssertionError as error:
                spider.logger.warning(
                    f"ChapterItem 检查失败: \n'{item!r}' -> {error}",
                )
                raise DropItem(str(error)) from error
            spider.logger.debug(f"ChapterItem 检查通过: '{item!r}'")
            return item
        # 若二者都不是则 Item 类型存在错误, 丢弃该 Item
        spider.logger.warning(
            f"Item 检查失败: '{item!r}' 不是一个 BookItem 或 ChapterItem.",
        )
        raise DropItem(f"'{item!r}' 不是一个 BookItem 或 ChapterItem.")

    @staticmethod
    def check_book_item(item: BookItem, spider: GeneralSpider) -> BookItem:
        """检查 BookItem 的有效性和完整性."""
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
        for k, v in item["other_info"].items():
            assert isinstance(k, str),  "书籍其它信息的键不是字符串"
            assert isinstance(v, str),  "书籍其它信息的值不是字符串"
        for i in item["cover_urls"]:
            assert isinstance(i, str),  "书籍封面 URL 列表中的元素不是字符串"
        for i in item["covers"]:
            assert isinstance(i, dict), "书籍封面图片列表中的元素不是字典"
        # 非默认值检查
        assert item["title"]  != "Default Book",    "书籍标题不能是默认值"
        assert item["author"] != "Default Author",  "书籍作者不能是默认值"
        assert item["state"]  != "Unknown",         "书籍状态不能是默认值"
        assert item["desc"]   != "Default Desc",    "书籍简介不能是默认值"
        assert item["source"] != DEFAULT_URL,       "书籍来源不能是默认 URL"
        # 逻辑检查
        if len(item["cover_urls"]) != len(item["covers"]):
            spider.logger.warning(
                f"书籍 '{item["title"]}' 的封面 URL 列表和封面图片列表长度不一致: "
                f"{len(item["cover_urls"])} != {len(item["covers"])}",
            )
            item["cover_urls"] = []
            item["covers"]     = []
        assert item["state"] in ["完结", "连载", "断更", "未知"], \
            "书籍状态只能是'完结'、'连载'、'断更'、'未知'中的一种"
        # 返回检查通过的 Item
        return item

    @staticmethod
    def check_chapter_item(item: ChapterItem, spider: GeneralSpider) -> None:
        """检查 ChapterItem 的有效性和完整性."""
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
        for k, v in item["other_info"].items():
            assert isinstance(k, str),  "章节其它信息的键不是字符串"
            assert isinstance(v, str),  "章节其它信息的值不是字符串"

        # 非默认值检查
        assert item["book_hash"] != "0"*64,          "书籍哈希值不能是默认值"
        assert item["index"]     != -1,              "章节索引不能是默认值"
        assert item["title"]   != "Default Chapter", "章节标题不能是默认值"
        assert item["content"] != "Default Content", "章节内容不能是默认值"
        assert item["source"]  != DEFAULT_URL,       "章节来源不能是默认 URL"

        # 逻辑检查
        assert len(item["book_hash"]) == 64,  "书籍哈希字符值必须为 64 位"
        assert item["index"]          >= 0,   "章节索引不能为负数"
        assert item["update_time"]    >= 0.0, "章节更新时间不能为负数"

        # 其它检查
        if (len(item["content"]) <= 800) and \
            (spider.name != "fanqienovel_com"):
            spider.logger.warning(
                f"章节 '{item["title"]}' 的内容过短, 可能是抓取不完整: \n"
                f"{item["content"]}",
            )
