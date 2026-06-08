"""
readers/epub_reader.py — EPUB 文件读取器。

将 .epub 文件解析为统一的 Document 对象。
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from ebooklib import epub

from core.document import Chapter, Document, Section
from readers.base import BaseReader


class EpubReader(BaseReader):
    """EPUB 读取器。

    使用 ebooklib 解析 EPUB，BeautifulSoup 提取文本和结构。
    """

    # HTML 中视为章节分隔的标题标签
    _HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    # 非内容型 media-type 前缀（图片、字体、样式等）
    _SKIP_MEDIA_PREFIXES = (
        "image/",
        "font/",
        "application/vnd.ms-opentype",
        "application/x-font",
        "text/css",
        "application/xml",
    )

    @staticmethod
    def supported_formats() -> list[str]:
        return ["epub"]

    def read(self, path: str | Path) -> Document:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"EPUB 文件不存在: {path}")

        book = epub.read_epub(str(path))

        doc = Document(
            title=self._extract_title(book, path),
            author=self._extract_author(book),
            source_format="epub",
            source_path=str(path.resolve()),
            metadata=self._extract_metadata(book),
        )

        spine_items = self._get_content_items(book)
        for index, item in enumerate(spine_items):
            chapter = self._parse_item(item, index)
            if chapter and chapter.sections:
                doc.chapters.append(chapter)

        # 如果没有任何章节（极端情况），创建单章
        if not doc.chapters:
            ch = doc.add_chapter(doc.title or "Untitled")
            ch.add_section(None, "[无法提取文本内容]")

        return doc

    # ------------------------------------------------------------------
    # metadata extraction
    # ------------------------------------------------------------------

    def _extract_title(self, book: epub.EpubBook, path: Path) -> str:
        titles = book.get_metadata("DC", "title")
        if titles:
            return str(titles[0][0])
        return path.stem  # fallback: 文件名

    def _extract_author(self, book: epub.EpubBook) -> str:
        creators = book.get_metadata("DC", "creator")
        if creators:
            return str(creators[0][0])
        return ""

    def _extract_metadata(self, book: epub.EpubBook) -> dict:
        meta: dict[str, str] = {}
        for name in ("language", "publisher", "date", "description"):
            values = book.get_metadata("DC", name)
            if values:
                meta[name] = str(values[0][0])
        return meta

    # ------------------------------------------------------------------
    # spine processing
    # ------------------------------------------------------------------

    def _get_content_items(self, book: epub.EpubBook) -> list:
        """获取 spine 中的文档型 item（排除图片/字体/样式）。"""
        items = []
        for item_id, _linear in book.spine:
            item = book.get_item_with_id(item_id)
            if item is None:
                continue
            media_type = item.media_type or ""
            if not media_type.startswith(self._SKIP_MEDIA_PREFIXES):
                items.append(item)
        return items

    # ------------------------------------------------------------------
    # HTML parsing
    # ------------------------------------------------------------------

    def _parse_item(self, item, index: int) -> Chapter | None:
        """解析单个 spine item，提取章节和节。"""
        try:
            content = item.get_content()
        except Exception:
            return None

        # 解码字节
        if isinstance(content, bytes):
            try:
                html = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    html = content.decode("latin-1")
                except UnicodeDecodeError:
                    return None
        else:
            html = str(content)

        soup = BeautifulSoup(html, "lxml")

        # 移除脚本和样式
        for tag in soup(["script", "style", "nav", "head"]):
            tag.decompose()

        body = soup.find("body")
        if body is None:
            body = soup

        chapter_title = self._find_chapter_title(body, item, index)
        sections = self._extract_sections(body)

        if not sections:
            text = self._clean_text(body.get_text())
            if not text.strip():
                return None
            sections = [Section(index=0, title=None, content=text, level=0)]

        chapter = Chapter(index=index, title=chapter_title, sections=sections)
        return chapter

    def _find_chapter_title(self, body: Tag, item, index: int) -> str:
        """从 body 的第一个标题标签或 item 名称推断章节标题。"""
        first_heading = body.find(self._HEADING_TAGS)
        if first_heading:
            return self._clean_text(first_heading.get_text())

        # fallback: item 的文件名
        name = getattr(item, "get_name", lambda: "")()
        if name:
            stem = Path(name).stem
            stem = re.sub(r"[_-]", " ", stem)
            return stem.strip() or f"Chapter {index + 1}"

        return f"Chapter {index + 1}"

    def _extract_sections(self, body: Tag) -> list[Section]:
        """从 HTML body 提取 Section 列表，按标题标签分割。"""
        sections: list[Section] = []
        current_title: str | None = None
        current_level: int = 0
        current_parts: list[str] = []

        def flush():
            nonlocal current_title, current_level, current_parts
            content = self._clean_text(" ".join(current_parts))
            if content.strip():
                sections.append(
                    Section(
                        index=len(sections),
                        title=current_title,
                        content=content,
                        level=current_level,
                    )
                )
            current_title = None
            current_level = 0
            current_parts = []

        for element in body.descendants:
            if isinstance(element, Tag):
                if element.name in self._HEADING_TAGS:
                    flush()
                    current_title = self._clean_text(element.get_text())
                    current_level = int(element.name[1])
                    continue

                if element.name in ("p", "li", "td", "th", "blockquote", "pre", "div"):
                    text = element.get_text(separator=" ", strip=True)
                    if text:
                        current_parts.append(text)

            elif isinstance(element, NavigableString):
                text = str(element).strip()
                if text:
                    current_parts.append(text)

        flush()
        return sections

    # ------------------------------------------------------------------
    # text cleaning
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理提取的文本。"""
        # 合并连续空白
        text = re.sub(r"[ \t]+", " ", text)
        # 合并连续换行
        text = re.sub(r"\n{3,}", "\n\n", text)
        # 去除首尾空白
        text = text.strip()
        return text
