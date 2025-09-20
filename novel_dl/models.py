#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# @FileName: models.py
# @Time: 10/08/2025 09:07
# @Author: Amundsen Severus Rubeus Bjaaland


# 导入第三方库: SQLAlchemy 的类型注解支持, 关系, 声明式基类
from sqlalchemy.orm import Mapped
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
# 导入第三方库: SQLAlchemy 的约束条件
from sqlalchemy import UniqueConstraint, CheckConstraint
# 导入第三方库: SQLAlchemy 的数据类型
from sqlalchemy import String, Text, Integer, JSON, Float, LargeBinary


# 定义书籍表的主键字符串, 用于外键关联
BOOK_COLUMN_STRING = "books.book_hash"


class Base(DeclarativeBase):
    """SQLAlchemy 的声明式基类"""
    pass


class BookTable(Base):
    __tablename__ = "books"
    
    book_hash:  Mapped[str] = mapped_column(String(64), primary_key=True)
    title:      Mapped[str] = mapped_column(String(32), nullable=False  )
    author:     Mapped[str] = mapped_column(String(16), nullable=False  )
    state:      Mapped[int] = mapped_column(Integer(),  nullable=False  )

    extra_info: Mapped["ExtraInfoTable"]     = relationship(
        back_populates="book", uselist=False, cascade="all, delete-orphan"
    )
    covers:     Mapped[list["CoverTable"]]   = relationship(
        back_populates="book",
    )
    chapters:   Mapped[list["ChapterTable"]] = relationship(
        back_populates="book",
    )
    
    __table_args__ = (
        UniqueConstraint("title", "author", name="uq_title_author"),
        CheckConstraint(state.in_([0, 1, 2, 3]), name="ck_state_valid"),
    )
    
    def __repr__(self):
        return "<BookRecord(in BookTable) " \
            f"title={self.title} author={self.author} " \
            f"length={len(self.chapters)}>"


class ExtraInfoTable(Base):
    __tablename__ = "extra_info"
    
    book_hash:  Mapped[str]  = mapped_column(
        String(64), ForeignKey(
            BOOK_COLUMN_STRING, ondelete="CASCADE"
        ), primary_key=True
    )
    desc:       Mapped[str]       = mapped_column(Text(), nullable=False)
    tags:       Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    sources:    Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    other_info: Mapped[dict]      = mapped_column(JSON(), nullable=False)
    
    book: Mapped[BookTable] = relationship(back_populates="extra_info")
    
    def __repr__(self):
        return "<ExtraInfoRecord(in ExtraInfoTable) " \
            f"book={self.book.title} desc={self.desc[:20]}...>"


class CoverTable(Base):
    __tablename__ = "covers"
    
    cover_hash: Mapped[str]   = mapped_column(String(64),     primary_key=True)
    source:     Mapped[str]   = mapped_column(String(2048),   nullable=False  )
    cover:      Mapped[bytes] = mapped_column(LargeBinary(),  nullable=False  )
    
    book_hash = mapped_column(ForeignKey(BOOK_COLUMN_STRING), nullable=False  )
    book: Mapped[BookTable] = relationship(back_populates="covers")
    
    def __repr__(self):
        return f"<CoverRecord(in CoverTable) book={self.book.title}>"


class ChapterTable(Base):
    __tablename__ = "chapters"
    
    chapter_hash: Mapped[str]   = mapped_column(String(64),   primary_key=True)
    index:        Mapped[int]   = mapped_column(Integer(),    nullable=False  )
    title:        Mapped[str]   = mapped_column(String(32),   nullable=False  )
    update_time:  Mapped[float] = mapped_column(Float(),      nullable=False  )
    
    content: Mapped["ContentTable"] = relationship(
        back_populates="chapter", uselist=False, cascade="all, delete-orphan"
    )
    
    book_hash = mapped_column(ForeignKey(BOOK_COLUMN_STRING), nullable=False  )
    book: Mapped[BookTable] = relationship(back_populates="chapters")
    
    __table_args__ = (
        UniqueConstraint("book_hash", "index", name="uq_book_index"),
        CheckConstraint(index > 0, name="ck_index_non_negative"),
        CheckConstraint(index <= 10000, name="ck_index_max_value"),
    )
    
    def __repr__(self) -> str:
        return "<ChapterRecord(in ChapterTable) " \
            f"book={self.book.title} index={self.index} title={self.index}>"


class ContentTable(Base):
    __tablename__ = "contents"
    
    chapter_hash: Mapped[str] = mapped_column(
        String(64), ForeignKey(
            'chapters.chapter_hash', ondelete="CASCADE"
        ), primary_key=True
    )
    content:      Mapped[str]       = mapped_column(Text(), nullable=False)
    sources:      Mapped[list[str]] = mapped_column(JSON(), nullable=False)
    other_info:   Mapped[dict]      = mapped_column(JSON(), nullable=False)
    
    chapter: Mapped[ChapterTable] = relationship(back_populates="content")
    
    def __repr__(self):
        return "<ContentRecord(in ContentTable)" \
            f"chapter={self.chapter.title} length={len(self.content)}>"
