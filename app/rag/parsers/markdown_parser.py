from __future__ import annotations

import re

from app.rag.ir import TreeNode
from app.rag.parsers.base import BaseParser

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


class MarkdownParser(BaseParser):
    """按 Markdown 标题层级解析为树结构。"""

    def parse(self, text: str, title: str = "") -> TreeNode:
        root = TreeNode(title=title or "文档", level=-1)
        if not text or not text.strip():
            return root

        lines = text.split("\n")
        # Stack of (level, node). Root is always at bottom.
        stack: list[tuple[int, TreeNode]] = [(-1, root)]
        current_lines: list[str] = []

        def _flush_content():
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    node = stack[-1][1]
                    node.content = (node.content + "\n" + content).strip() if node.content else content
                current_lines.clear()

        for line in lines:
            m = _HEADING_RE.match(line.strip())
            if m:
                _flush_content()
                level = len(m.group(1))
                heading_title = m.group(2).strip()
                node = TreeNode(title=heading_title, level=level)

                # Pop stack until we find a parent (level < current)
                while len(stack) > 1 and stack[-1][0] >= level:
                    stack.pop()

                stack[-1][1].children.append(node)
                stack.append((level, node))
            else:
                current_lines.append(line)

        _flush_content()
        return root
