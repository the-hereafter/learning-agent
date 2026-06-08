"""
readers/base.py — Reader 抽象基类。

所有格式的 Reader 继承 BaseReader，实现 read() 方法。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.document import Document


class BaseReader(ABC):
    """文档读取器基类。

    子类只需实现：
      - read(path) → Document
      - supported_formats() → list[str]
    """

    @abstractmethod
    def read(self, path: str | Path) -> Document:
        """读取文件，返回统一 Document 对象。

        Args:
            path: 文件路径

        Returns:
            Document 对象（title, author, chapters 已填充）

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式不支持或文件损坏
        """
        ...

    @staticmethod
    @abstractmethod
    def supported_formats() -> list[str]:
        """返回支持的扩展名列表，如 ['epub']。"""
        ...

    def can_handle(self, path: str | Path) -> bool:
        """判断此 Reader 是否能处理该文件。"""
        suffix = Path(path).suffix.lower().lstrip(".")
        return suffix in self.supported_formats()
