# 小说下载器

该项目是一个用于从各种在线小说网站下载小说的工具. 该项目基于 Python 的 Scrapy 框架.

## 使用

目前仅支持直接给出小说详情页 URL 的方式下载小说.

安装必要的 Python 库以后, 使用 `scrapy crawl <spider_name>` 命令运行爬虫, 例如:

```bash
scrapy crawl xiaxs_com -a novel_url=https://www.xiaxs.com/xs/92156/ -o output.epub
```

受限于 Scrapy 框架, 目前只能通过命令行运行爬虫, 且命令比较复杂.

## 支持的网站

- [笔趣阁](https://www.xiaxs.com/)
