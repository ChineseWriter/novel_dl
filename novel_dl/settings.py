#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: settings.py
# @Time: 19/07/2025 17:11
# @Author: Amundsen Severus Rubeus Bjaaland
"""novel_dl 的 Scrapy 设置文件.

## 说明
为简洁起见, 此文件仅包含被视为重要或常用的设置. 你可以查阅文档获取更多设置:
1. https://docs.scrapy.org/en/latest/topics/settings.html
2. https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
3. https://docs.scrapy.org/en/latest/topics/spider-middleware.html

## 设置分类
1. 基础设置: 包括爬虫名称、日志级别、Telnet控制台.
2. 爬虫模块设置: 包括 Spider 模块的位置.
3. 反爬相关设置: 包括 User-Agent、robots.txt、Cookie、下载超时、请求头.
4. 重新下载设置: 包括重新下载功能开关、重试次数、HTTP 错误码、重新下载的优先级.
5. 图片下载设置: 包括图片 URL 字段名、图片下载结果字段名、图片存储路径、过期时间.
6. Item 与 Pipeline 设置: 包括默认 Item 类、并发 Item 数量、启用的 Item 管道.
7. 自动节流扩展: 包括启用状态、初始下载延迟、最大下载延迟、目标并发请求数、调试模式.
8. 请求并发设置: 包括最大并发请求数、每个域名的最大并发请求数、
   每个 IP 地址的最大并发请求数、下载延迟.
9. 下载流程控制设置: 包括启用的爬虫中间件、下载中间件、扩展.
10. HTTP 缓存设置: 包括启用状态、缓存过期时间、
   缓存目录、忽略的 HTTP 错误码、缓存存储方式.
11. 请求去重相关设置: 包括 URL 去重方法、Reactor 设置.
12. 导出相关设置: 包括导出格式与对应的导出器、文件系统存储选项.
"""


# 导入标准库
from pathlib import Path


# 基础设置
BOT_NAME = "novel_dl"         # 爬虫的名字, 该名称也用于日志记录
LOG_LEVEL = "INFO"            # 设置日志级别(默认值: DEBUG)
TELNETCONSOLE_ENABLED = True  # 是否启用 Telnet 控制台(默认启用)
DATA_DIR = Path(Path.cwd()) / "data"   # 数据存储目录, 用于存储图片、数据库等数据
DB_URI = "sqlite:///data/novel_dl.db"  # 数据库 URI, 用于存储书籍和章节信息


# 爬虫模块设置
SPIDER_MODULES = ["novel_dl.spiders"]  # 保存 Spider 的位置列表
NEWSPIDER_MODULE = "novel_dl.spiders"  # 设置在哪里创建新的 Spider


# 反爬相关设置
USER_AGENT = (                     # 设置 User-Agent 字符串, 用于模拟浏览器
   "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) "
   "Gecko/20100101 Firefox/140.0"
)
ROBOTSTXT_OBEY = False             # 是否遵守 robots.txt 的条款
COOKIES_ENABLED = True             # 是否启用 Cookie(默认启用)
DOWNLOAD_TIMEOUT = 25              # 下载的超时限制
# DEFAULT_REQUEST_HEADERS = {        # 覆盖默认的请求头
#    "Accept": "text/html,application/xhtml+xml," \
#       "application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "zh-CN,zh",
# }


# 重新下载设置
RETRY_ENABLED = True        # 重新下载功能(默认启用)
RETRY_TIMES = 5             # 设置重新下载的最大次数(默认值: 2)
RETRY_HTTP_CODES = [        # 设置触发重新下载功能的 HTTP 错误码
   500, 502, 503, 504, 408, 403, 404,
]                           # (默认值: 500, 502, 503, 504, 408)
# RETRY_PRIORITY_ADJUST = -1  # 设置重新下载的延迟时间(默认值: 0)


# 图片下载设置
IMAGES_URLS_FIELD = "cover_urls"      # 图片 URL 字段名
IMAGES_RESULT_FIELD = "covers"        # 图片下载结果字段名
IMAGES_STORE = DATA_DIR / "cache" / "images"  # 图片存储路径
IMAGES_EXPIRES = 5                    # 图片过期时间(单位: 天), 默认值: 90


# Item 与 Pipeline 设置
# 设置默认的 Item, 该默认的 Item 将用于 Scrapy shell 实例化.
DEFAULT_ITEM_CLASS = "scrapy.Item"
CONCURRENT_ITEMS = 50          # 设置同一个管道内同时可存在的最大 Item 数量
ITEM_PIPELINES = {             # 设置 Item 的管道
   "scrapy.pipelines.images.ImagesPipeline": 1,
   "novel_dl.pipelines.check.CheckPipeline": 2,
   "novel_dl.pipelines.db.DBPipeline": 100,
   "novel_dl.pipelines.verify.VerifyPipeline": 150,
}  # 文档: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# 自动节流扩展(默认禁用), 文档:
#  https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True   # 是否启用 AutoThrottle 扩展
AUTOTHROTTLE_START_DELAY = 5  # 初始下载延迟
AUTOTHROTTLE_MAX_DELAY = 60   # 在高延迟情况下设置的最大下载延迟
# Scrapy 应并行发送到每个远程服务器的平均请求数
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False    # 启用为每个接收到的响应显示节流统计信息


# 请求并发设置
# 配置 Scrapy 执行的最大并发请求数(默认值: 16).
CONCURRENT_REQUESTS = 32
# 配置每个域名的最大并发请求数(默认值: 16)
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# 配置每个 IP 地址的最大并发请求数(默认值: 16),
# 注意: 如果该设置项不为 0, 则以上"PER_DOMAIN"设置会被忽略
# 且 DOWNLOAD_DELAY 和 AutoThrottle 设置会变为针对 IP 而非域名.
# CONCURRENT_REQUESTS_PER_IP = 16
# 配置对同一网站请求的延迟时间(默认值: 0), 文档:
#  https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# DOWNLOAD_DELAY = 3


# 下载流程控制设置
SPIDER_MIDDLEWARES: dict = {      # 启用的爬虫中间件
}  # 文档: https://docs.scrapy.org/en/latest/topics/spider-middleware.html
DOWNLOADER_MIDDLEWARES: dict = {  # 启用的下载中间件
}  # 文档: https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
EXTENSIONS: dict = {              # 启用的扩展
}  # 文档: https://docs.scrapy.org/en/latest/topics/extensions.html


# 启用并设置 HTTP 缓存(默认禁用), 文档:
#  https://docs.scrapy.org/en/latest/topics/downloader-middleware.html \
#  #httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"


# 请求去重相关设置
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"  # 设置使用的 URL 去重方法
TWISTED_REACTOR = (        # 设置使用的 Reactor, 该设置基于 Twisted 框架
   "twisted.internet.asyncioreactor."
   "AsyncioSelectorReactor"
)

# 导出相关设置
FEED_EXPORTERS = {                            # 设置导出格式与对应的导出器
   "txt": "novel_dl.exporters.TxtExporter",
   "epub": "novel_dl.exporters.EpubExporter",
}
