"""
core/document.py — 统一文档模型。

所有文件格式（EPUB/PDF/HTML/Markdown/TXT）最终都转换为 Document 对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Section:
    """文档中的一节。

    一个 Section 是 Chapter 内部的一个逻辑片段，
    通常由标题（h1-h6）或空行分隔。
    """

    index: int
    title: str | None  # None 表示无标题节（如开篇引文）
    content: str       # 已清理的纯文本
    level: int = 1     # 标题层级 1-6，无标题时为 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        title_preview = (self.title or "<untitled>")[:40]
        content_preview = self.content[:60].replace("\n", " ")
        return f"Section({self.index}, L{self.level}, '{title_preview}', '{content_preview}...')"


@dataclass
class Chapter:
    """文档中的一章。

    对于 EPUB：每个 spine item 映射为一个 Chapter。
    对于 TXT/Markdown：整个文件为一个 Chapter，或按 # 标题分割。
    """

    index: int
    title: str
    sections: list[Section] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def raw_text(self) -> str:
        """将本章所有 Section 拼接为连续文本。"""
        parts: list[str] = []
        for sec in self.sections:
            if sec.title:
                parts.append(sec.title)
            parts.append(sec.content)
        return "\n\n".join(parts)

    def add_section(self, title: str | None, content: str, level: int = 1) -> Section:
        sec = Section(
            index=len(self.sections),
            title=title,
            content=content,
            level=level,
        )
        self.sections.append(sec)
        return sec

    def __repr__(self) -> str:
        return f"Chapter({self.index}, '{self.title[:40]}', {len(self.sections)} sections)"


@dataclass
class Document:
    """统一文档模型。

    所有 Reader 的最终产出。包含从任何格式提取的结构化内容。
    """

    title: str
    author: str = ""
    chapters: list[Chapter] = field(default_factory=list)
    source_format: str = "unknown"   # epub, pdf, html, markdown, txt
    source_path: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def raw_text(self) -> str:
        """完整的文档纯文本（所有章节拼接）。"""
        parts: list[str] = []
        for ch in self.chapters:
            if ch.title:
                parts.append(f"# {ch.title}")
            parts.append(ch.raw_text)
        return "\n\n".join(parts)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def section_count(self) -> int:
        return sum(len(ch.sections) for ch in self.chapters)

    def add_chapter(self, title: str) -> Chapter:
        ch = Chapter(index=len(self.chapters), title=title)
        self.chapters.append(ch)
        return ch

    def to_dict(self) -> dict[str, Any]:
        """将 Document 序列化为可 JSON 化的 dict（供 Step 2 消费）。"""
        return {
            "title": self.title,
            "author": self.author,
            "source_format": self.source_format,
            "source_path": self.source_path,
            "metadata": self.metadata,
            "chapters": [
                {
                    "index": ch.index,
                    "title": ch.title,
                    "sections": [
                        {
                            "index": sec.index,
                            "title": sec.title,
                            "content": sec.content,
                            "level": sec.level,
                        }
                        for sec in ch.sections
                    ],
                }
                for ch in self.chapters
            ],
        }

    def __repr__(self) -> str:
        return (
            f"Document('{self.title[:50]}', {self.source_format}, "
            f"{self.chapter_count} chapters, {self.section_count} sections)"
        )
