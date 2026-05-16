from __future__ import annotations

from app.rag.ir import TreeNode
from app.rag.parsers.base import BaseParser


class PlainParser(BaseParser):
    """无结构文档的兜底解析器。整个文档作为单节点。"""

    def parse(self, text: str, title: str = "") -> TreeNode:
        root = TreeNode(title=title or "文档内容", level=-1)
        if text and text.strip():
            root.content = text.strip()
        return root
