from __future__ import annotations

from abc import ABC, abstractmethod

from app.rag.ir import TreeNode


class BaseParser(ABC):
    """文档结构解析器基类"""

    @abstractmethod
    def parse(self, text: str, title: str = "") -> TreeNode:
        """解析文档文本，返回虚拟根节点 (level=-1)。"""
