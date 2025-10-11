#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: fanqienovel_com.py
# @Time: 10/10/2025 18:26
# @Author: Amundsen Severus Rubeus Bjaaland
"""fanqienovel.com 小说爬虫."""

import copy
import random
import re
import time
from logging import LoggerAdapter
from multiprocessing import Queue
from threading import Lock, Thread
from typing import Generator, Iterable

import requests
from bs4 import BeautifulSoup as bs
from itemloaders.processors import MapCompose
from scrapy.http import Request, Response

from novel_dl.entity.items import BookItem, ChapterItem
from novel_dl.templates import BookItemLoader, GeneralSpider
from novel_dl.templates import ChapterItemLoader as CIL


PASSWORD_CODE = [[58344, 58715], [58345, 58716]]
CIPHER_TEXT = [
    [
        "D", "在", "主", "特", "家", "军", "然", "表", "场", "4", "要", "只", "v",
        "和", "?", "6", "别", "还", "g", "现", "儿", "岁", "?", "?", "此", "象",
        "月", "3", "出", "战", "工", "相", "o", "男", "直", "失", "世", "F", "都",
        "平", "文", "什", "V", "O", "将", "真", "T", "那", "当", "?", "会", "立",
        "些", "u", "是", "十", "张", "学", "气", "大", "爱", "两", "命", "全", "后",
        "东", "性", "通", "被", "1", "它", "乐", "接", "而", "感", "车", "山", "公",
        "了", "常", "以", "何", "可", "话", "先", "p", "i", "叫", "轻", "M", "士",
        "w", "着", "变", "尔", "快", "l", "个", "说", "少", "色", "里", "安", "花",
        "远", "7", "难", "师", "放", "t", "报", "认", "面", "道", "S", "?", "克",
        "地", "度", "I", "好", "机", "U", "民", "写", "把", "万", "同", "水", "新",
        "没", "书", "电", "吃", "像", "斯", "5", "为", "y", "白", "几", "日", "教",
        "看", "但", "第", "加", "候", "作", "上", "拉", "住", "有", "法", "r", "事",
        "应", "位", "利", "你", "声", "身", "国", "问", "马", "女", "他", "Y", "比",
        "父", "x", "A", "H", "N", "s", "X", "边", "美", "对", "所", "金", "活",
        "回", "意", "到", "z", "从", "j", "知", "又", "内", "因", "点", "Q", "三",
        "定", "8", "R", "b", "正", "或", "夫", "向", "德", "听", "更", "?", "得",
        "告", "并", "本", "q", "过", "记", "L", "让", "打", "f", "人", "就", "者",
        "去", "原", "满", "体", "做", "经", "K", "走", "如", "孩", "c", "G", "给",
        "使", "物", "?", "最", "笑", "部", "?", "员", "等", "受", "k", "行", "一",
        "条", "果", "动", "光", "门", "头", "见", "往", "自", "解", "成", "处",
        "天", "能", "于", "名", "其", "发", "总", "母", "的", "死", "手", "入",
        "路", "进", "心", "来", "h", "时", "力", "多", "开", "已", "许", "d", "至",
        "由", "很", "界", "n", "小", "与", "Z", "想", "代", "么", "分", "生", "口",
        "再", "妈", "望", "次", "西", "风", "种", "带", "J", "?", "实", "情", "才",
        "这", "?", "E", "我", "神", "格", "长", "觉", "间", "年", "眼", "无", "不",
        "亲", "关", "结", "0", "友", "信", "下", "却", "重", "己", "老", "2", "音",
        "字", "m", "呢", "明", "之", "前", "高", "P", "B", "目", "太", "e", "9",
        "起", "稜", "她", "也", "W", "用", "方", "子", "英", "每", "理", "便", "四",
        "数", "期", "中", "C", "外", "样", "a", "海", "们", "任",
    ],
    [
        "s", "?", "作", "口", "在", "他", "能", "并", "B", "士", "4", "U", "克",
        "才", "正", "们", "字", "声", "高", "全", "尔", "活", "者", "动", "其",
        "主", "报", "多", "望", "放", "h", "w", "次", "年", "?", "中", "3", "特",
        "于", "十", "入", "要", "男", "同", "G", "面", "分", "方", "K", "什", "再",
        "教", "本", "己", "结", "1", "等", "世", "N", "?", "说", "g", "u", "期",
        "Z", "外", "美", "M", "行", "给", "9", "文", "将", "两", "许", "张", "友",
        "0", "英", "应", "向", "像", "此", "白", "安", "少", "何", "打", "气", "常",
        "定", "间", "花", "见", "孩", "它", "直", "风", "数", "使", "道", "第",
        "水", "已", "女", "山", "解", "d", "P", "的", "通", "关", "性", "叫", "儿",
        "L", "妈", "问", "回", "神", "来", "S", "", "四", "望", "前", "国", "些",
        "O", "v", "l", "A", "心", "平", "自", "无", "军", "光", "代", "是", "好",
        "却", "c", "得", "种", "就", "意", "先", "立", "z", "子", "过", "Y", "j",
        "表", "", "么", "所", "接", "了", "名", "金", "受", "J", "满", "眼", "没",
        "部", "那", "m", "每", "车", "度", "可", "R", "斯", "经", "现", "门", "明",
        "V", "如", "走", "命", "y", "6", "E", "战", "很", "上", "f", "月", "西",
        "7", "长", "夫", "想", "话", "变", "海", "机", "x", "到", "W", "一", "成",
        "生", "信", "笑", "但", "父", "开", "内", "东", "马", "日", "小", "而",
        "后", "带", "以", "三", "几", "为", "认", "X", "死", "员", "目", "位", "之",
        "学", "远", "人", "音", "呢", "我", "q", "乐", "象", "重", "对", "个", "被",
        "别", "F", "也", "书", "稜", "D", "写", "还", "因", "家", "发", "时", "i",
        "或", "住", "德", "当", "o", "l", "比", "觉", "然", "吃", "去", "公", "a",
        "老", "亲", "情", "体", "太", "b", "万", "C", "电", "理", "?", "失", "力",
        "更", "拉", "物", "着", "原", "她", "工", "实", "色", "感", "记", "看",
        "出", "相", "路", "大", "你", "候", "2", "和", "?", "与", "p", "样", "新",
        "只", "便", "最", "不", "进", "T", "r", "做", "格", "母", "总", "爱", "身",
        "师", "轻", "知", "往", "加", "从", "?", "天", "e", "H", "?", "听", "场",
        "由", "快", "边", "让", "把", "任", "8", "条", "头", "事", "至", "起", "点",
        "真", "手", "这", "难", "都", "界", "用", "法", "n", "处", "下", "又", "Q",
        "告", "地", "5", "k", "t", "岁", "有", "会", "果", "利", "民",
    ],
]


def _decrypt(code: int, mode: int) -> str:
    if PASSWORD_CODE[mode][0] <= code <= PASSWORD_CODE[mode][1]:
        new_code = code - PASSWORD_CODE[mode][0]
        if (0 <= new_code < len(CIPHER_TEXT[mode])
            and CIPHER_TEXT[mode][new_code] != "?"):
                    return CIPHER_TEXT[mode][new_code]
    return chr(code)


def deal_content(content: str) -> str | None:
    """处理章节内容."""
    html = bs(content, "lxml")
    paras = html.find_all("p")
    paras = [p.get_text() for p in paras]
    paras = list(filter(lambda x: bool(x.strip()), paras))
    data = "\t" + "\n\t".join(paras)
    buffer = []
    for one_char in data:
        char_unicode = ord(one_char)
        try: buffer.append(_decrypt(char_unicode, 0))
        except Exception as e:
            try:
                buffer.append(_decrypt(char_unicode, 1))
            except Exception as e:
                return None
    return "".join(buffer)


class CookieGenerator:
    """生成访问 cookie."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) "
            "Gecko/20100101 Firefox/140.0",
    }

    def __init__(
            self, logger: LoggerAdapter | None = None, # type: ignore[reportMissingTypeArgument]
        ) -> None:
        """初始化 Cookie 生成器."""
        self.__active_cookie: int = 1000000000000000000
        self.__cookies: Queue[int] = Queue(5)
        self.__flag = True
        self.__lock = Lock()
        self.__logger = logger

        self.__main_thread = Thread(
            target=self.__generate, name="Cookie 生成线程",
        )
        self.__main_thread.start()

    def __del__(self) -> None:
        """析构函数, 停止线程."""
        self.__flag = False

    def __generate(self) -> None:
        while self.__flag:
            base = 1000000000000000000
            for i in range(random.randint(base * 6, base * 8), base * 9):
                time.sleep(random.randint(50, 150) / 1000)
                if self.__test(i):
                    self.__cookies.put(i)
                    continue

    def __test(self, cookie: int) -> bool:
        """测试 cookie 是否有效."""
        headers = copy.deepcopy(self.HEADERS)
        headers["cookie"] = f"novel_web_id={cookie}"
        response = requests.get(
            "https://fanqienovel.com/reader/7251588723630932491",
            headers=headers, timeout=21,
        )
        if response.status_code != 200:
            return False
        html = bs(response.text, "lxml")
        content = html.find("div", class_="muye-reader-content noselect")
        if content is None:
            return False
        return not len(content.get_text(strip=True)) < 200

    def get_cookie(self, old: int) -> int:
        """获取一个可用的 cookie."""
        cookie = 1000000000000000000
        with self.__lock:
            if old == self.__active_cookie:
                self.__active_cookie = self.__cookies.get()
                if self.__logger is not None:
                    self.__logger.info(f"更新 cookie 为 {self.__active_cookie}.")
            cookie = copy.deepcopy(self.__active_cookie)
        return cookie  # noqa: RET504


class ChapterItemLoader(CIL):
    """章节信息数据加载器."""

    title_in = MapCompose(str.strip, lambda x: x.split(" ")[-1])
    update_time_in = MapCompose(str.strip, lambda x: time.mktime(time.strptime(x, "%Y-%m-%d")), float)
    content_in = MapCompose(str.strip, deal_content)


class FanqieSpider(GeneralSpider):
    """fanqienovel.com 小说爬虫."""

    name = "fanqienovel_com"
    domain = "www.fanqienovel.com"
    book_url_pattern = re.compile(r"^/page/\d+$")
    chapter_url_pattern = re.compile(r"^/reader/\d+$")

    def __init__(self, novel_url: str | None = None) -> None:
        """初始化爬虫实例."""
        super().__init__(novel_url)

        self.__cookie_generator = CookieGenerator(self.logger)

    def transform(
            self, response: Response,
        ) -> None | Generator[Request, None, None]:
        """转换章节列表页面, 获取章节列表并生成章节请求."""
        # 获取章节列表
        result = self.get_chapter_list(response)
        # 如果章节列表获取失败, 则返回 None.
        if result is None: return None

        # 取出用于传递章节索引的变量
        index: int = response.meta["index"]
        # 检查链接列表中是否存在章节详情页链接
        content_request: Request | None = None
        # 获取一个可用的 cookie
        cookie = self.__cookie_generator.get_cookie(1000000000000000000)
        # 遍历章节列表, 生成章节请求.
        for i in result:
            # 如果链接不是章节详情页, 则将其作为新的章节列表请求返回.
            if not self.chapter_url_pattern.match(i):
                content_request = response.follow(
                    i, self.__transform, priority=10,
                    meta={"book_hash": response.meta["book_hash"]},
                )
                continue
            # 如果链接是章节详情页, 则生成章节请求.
            request = response.follow(
                i, self.get_chapter_info, priority=5,
                cookies={"novel_web_id": str(cookie)},
                meta={
                    "book_hash": response.meta["book_hash"],
                    "index": index,
                },
            )
            self.chapters_crawled[response.meta["book_hash"]] += 1
            index += 1
            yield request

        # 如果所有链接均为章节详情页, 则将 chapter_list_flag 设为 True.
        if content_request is None:
            self.chapter_list_flag[response.meta["book_hash"]] = True
            self.logger.info(
                f"书籍 {response.meta['book_hash'][:8]} 的章节列表获取完成, "
                f"共计 {self.chapters_crawled[response.meta['book_hash']]} 章.",
            )
        # 如果章节列表中存在新的章节列表请求, 则将其返回.
        else:
            content_request.meta["index"] = index
            yield content_request

    def get_book_info(self, response: Response) -> BookItem | None:
        """获取书籍信息."""
        html = self.get_html(response)
        if html is None:
            return None
        loader = BookItemLoader(item=BookItem(), selector=html)
        loader.add_xpath("title", "//h1[1]/text()")
        loader.add_xpath("author", '//span[@class="author-name-text"][1]/text()')
        loader.add_xpath("cover_urls", '//img[@class="book-cover-img"]/@src')
        loader.add_xpath("state", '//div[@class="info-label"]/span[1]/text()')
        loader.add_xpath("desc", '//div[@class="page-abstract-content"]/p/text()')
        loader.add_value("source", response.url)
        loader.add_value("other_info", {"fq_id": response.url.split("/")[-1]})
        item = loader.load_item()
        if isinstance(item["other_info"], list):
            item["other_info"] = item["other_info"][0]
        return item

    def get_chapter_list(self, response: Response) -> Iterable[str] | None:
        """获取章节列表."""
        yield from response.xpath('//div[@class="page-directory-content"]//a/@href').getall()

    def get_chapter_info(  # type: ignore[reportIncompatibleMethodOverride]
            self, response: Response,
        ) -> ChapterItem | Request | None:
        """获取章节信息."""
        html = self.get_html(response)
        if html is None:
            return None
        loader = ChapterItemLoader(item=ChapterItem(), selector=html)
        loader.add_value("book_hash", response.meta["book_hash"])
        loader.add_value("index", response.meta["index"])
        loader.add_xpath("title", '//h1[@class="muye-reader-title"]/text()')
        loader.add_xpath("content", '//div[@class="muye-reader-content noselect"]//div')
        loader.add_value("source", response.url)
        loader.add_xpath(
            "update_time",
            '//div[@class="muye-reader-subtitle"]//span[@class="desc-item"][2]/text()',
        )
        item = loader.load_item()
        if len(item.get("content", "")) < 200:
            request = response.request
            if request is None:
                old_cookie = 1000000000000000000
            else:
                old_cookie = request.headers.get("cookie", b"1000000000000000000")
            if old_cookie is None:
                old_cookie = b"1000000000000000000"
            old_cookie = old_cookie.decode("ASCII")
            old_cookie = old_cookie.split("=")[-1]
            cookie = self.__cookie_generator.get_cookie(int(old_cookie))
            return Request(
                response.url, self.get_chapter_info, priority=5,
                cookies={"novel_web_id": str(cookie)},
                meta={
                    "book_hash": response.meta["book_hash"],
                    "index": response.meta["index"],
                },
                dont_filter=True,
            )
        return loader.load_item()
