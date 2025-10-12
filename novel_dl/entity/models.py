#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: models.py
# @Time: 10/08/2025 09:07
# @Author: Amundsen Severus Rubeus Bjaaland
"""数据库模型类, 用于支持 SQLAlchemy ORM 操作."""


# 导入第三方库
from sqlalchemy import (  # noqa: I001
    JSON, CheckConstraint, Float, ForeignKey, Integer,
    LargeBinary, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# 定义书籍表的主键字符串, 用于外键关联
BOOK_COLUMN_STRING = "books.book_hash"


class Base(DeclarativeBase):
    """SQLAlchemy 的声明式基类."""


class BookTable(Base):
    """书籍表, 用于存储书籍的基本信息."""

    # 设置在数据库中的表名
    __tablename__ = "books"
    # 定义表中的各个字段
    book_hash:  Mapped[str]            = mapped_column(String(64),   primary_key=True)
    title:      Mapped[str]            = mapped_column(String(64),   nullable=False  )
    author:     Mapped[str]            = mapped_column(String(32),   nullable=False  )
    state:      Mapped[int]            = mapped_column(Integer(),    nullable=False  )
    desc:       Mapped[str]            = mapped_column(String(1024), nullable=False  )
    tags:       Mapped[list[str]]      = mapped_column(JSON(),       nullable=False  )
    other_info: Mapped[dict[str, str]] = mapped_column(JSON(),       nullable=False  )
    # 定义一对多的关系
    sources: Mapped[list["BookSourceTable"]] = relationship(
        back_populates="book", cascade="all, delete-orphan",
    )
    covers:     Mapped[list["CoverTable"]]   = relationship(
        back_populates="book", cascade="all, delete-orphan",
    )
    chapters:   Mapped[list["ChapterTable"]] = relationship(
        back_populates="book", cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("title", "author", name="uq_title_author"),
        CheckConstraint(state.in_([0, 1, 2, 3]), name="ck_state_valid"),
    )

    def __repr__(self) -> str:
        return ("<BookRecord(in BookTable) "
            f"title={self.title} author={self.author} "
            f"length={len(self.chapters)}>")


class BookSourceTable(Base):
    """书籍来源表, 用于存储书籍的来源信息."""

    # 设置在数据库中的表名
    __tablename__ = "book_sources"
    # 定义表中的各个字段
    url_hash:  Mapped[str] = mapped_column(String(64),     primary_key=True)
    url:       Mapped[str] = mapped_column(String(2048),   nullable=False  )
    # 定义与书籍表的外键关系
    book_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey(
            BOOK_COLUMN_STRING, ondelete="CASCADE",
        ), primary_key=True,
    )
    book: Mapped[BookTable] = relationship(back_populates="sources")

    def __repr__(self) -> str:
        return ("<BookSourceRecord(in BookSourceTable) "
            f"book={self.book.title} value={self.url}>")


class CoverTable(Base):
    """封面表, 用于存储书籍的封面图片."""

    # 设置在数据库中的表名
    __tablename__ = "covers"
    # 定义表中的各个字段
    cover_hash: Mapped[str]   = mapped_column(String(64),     primary_key=True)
    source:     Mapped[str]   = mapped_column(String(2048),   nullable=False  )
    image:      Mapped[bytes] = mapped_column(LargeBinary(),  nullable=False  )
    # 定义与书籍表的外键关系
    book_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey(
            BOOK_COLUMN_STRING, ondelete="CASCADE",
        ), primary_key=True,
    )
    book: Mapped[BookTable] = relationship(back_populates="covers")

    def __repr__(self) -> str:
        return ("<CoverRecord(in CoverTable) "
            f"book={self.book.title} hash={self.cover_hash[:8]}>")


class ChapterTable(Base):
    """章节表, 用于存储章节的基本信息."""

    # 设置在数据库中的表名
    __tablename__ = "chapters"
    # 定义表中的各个字段
    chapter_hash: Mapped[str]             = mapped_column(String(64),   primary_key=True)
    index:        Mapped[int]             = mapped_column(Integer(),    nullable=False  )
    title:        Mapped[str]             = mapped_column(String(64),   nullable=False  )
    update_time:  Mapped[float]           = mapped_column(Float(),      nullable=False  )
    content:      Mapped[str]             = mapped_column(Text(),       nullable=False  )
    other_info:   Mapped[dict[str, str]]  = mapped_column(JSON(),       nullable=False  )
    # 定义与书籍表的外键关系
    book_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey(
            BOOK_COLUMN_STRING, ondelete="CASCADE",
        ), primary_key=True,
    )
    book: Mapped[BookTable] = relationship(back_populates="chapters")
    # 定义一对多的关系
    sources: Mapped[list["ChapterSourceTable"]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("book_hash", "index", name="uq_book_index"),
        CheckConstraint(index > 0, name="ck_index_non_negative"),
        CheckConstraint(index <= 10000, name="ck_index_max_value"),
    )

    def __repr__(self) -> str:
        return ("<ChapterRecord(in ChapterTable) "
            f"book={self.book.title} index={self.index} title={self.index}>")


class ChapterSourceTable(Base):
    """章节来源表, 用于存储章节的来源信息."""

    # 设置在数据库中的表名
    __tablename__ = "chapter_sources"
    # 定义表中的各个字段
    url_hash:   Mapped[str] = mapped_column(String(64),   primary_key=True)
    url:        Mapped[str] = mapped_column(String(2048), nullable=False  )
    # 定义与章节表的外键关系
    chapter_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey(
            "chapters.chapter_hash", ondelete="CASCADE",
        ), primary_key=True,
    )
    chapter: Mapped[ChapterTable] = relationship(back_populates="sources")

    def __repr__(self) -> str:
        return ("<ChapterSourceRecord(in ChapterSourceTable) "
            f"chapter={self.chapter.title} desc={self.desc[:20]}...>")


class IndexTable(Base):
    """索引表, 用于存储搜索索引."""

    # 设置在数据库中的表名
    __tablename__ = "index"
    # 定义表中的各个字段
    hash_:     Mapped[str] = mapped_column(String(64), primary_key=True)
    word:      Mapped[str] = mapped_column(String(32), nullable=False  )
    book_hash: Mapped[str] = mapped_column(String(64), nullable=False  )

    def __repr__(self) -> str:
        return f"<IndexRecord(in IndexTable) keyword={self.keyword}>"
