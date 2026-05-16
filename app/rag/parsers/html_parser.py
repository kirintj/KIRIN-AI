from __future__ import annotations

import re
from html.parser import HTMLParser as _StdHTMLParser

from app.rag.ir import TreeNode
from app.rag.parsers.base import BaseParser


class _HeadingExtractor(_StdHTMLParser):
    """提取 HTML 中的标题标签和文本内容。"""

    def __init__(self):
        super().__init__()
        self.sections: list[tuple[int, str, list[str]]] = []  # (level, title, lines)
        self._current_level = -1
        self._current_title = ""
        self._current_lines: list[str] = []
        self._in_heading = False
        self._heading_level = 0

    def handle_starttag(self, tag, attrs):
        m = re.match(r"^h([1-6])$", tag, re.IGNORECASE)
        if m:
            self._flush()
            self._heading_level = int(m.group(1))
            self._in_heading = True
            self._current_level = self._heading_level

    def handle_endtag(self, tag):
        m = re.match(r"^h([1-6])$", tag, re.IGNORECASE)
        if m and self._in_heading:
            self._in_heading = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_heading:
            self._current_title += text
        else:
            self._current_lines.append(text)

    def _flush(self):
        if self._current_title and self._current_level > 0:
            self.sections.append((self._current_level, self._current_title, list(self._current_lines)))
        elif self._current_lines and self._current_level < 0:
            self.sections.append((-1, "", list(self._current_lines)))
        self._current_title = ""
        self._current_lines.clear()
        self._current_level = self._heading_level if self._in_heading else -1

    def finish(self):
        self._flush()
        return self.sections


class HtmlParser(BaseParser):
    """按 HTML 标题标签解析为树结构。"""

    def parse(self, text: str, title: str = "") -> TreeNode:
        root = TreeNode(title=title or "文档", level=-1)
        if not text or not text.strip():
            return root

        extractor = _HeadingExtractor()
        extractor.feed(text)
        sections = extractor.finish()

        if not sections:
            root.content = text.strip()
            return root

        # Build tree from flat sections
        stack: list[tuple[int, TreeNode]] = [(-1, root)]
        for level, sec_title, lines in sections:
            content = "\n".join(lines).strip()
            if level < 0:
                root.content = (root.content + "\n" + content).strip() if root.content else content
                continue

            node = TreeNode(title=sec_title, level=level, content=content)
            while len(stack) > 1 and stack[-1][0] >= level:
                stack.pop()
            stack[-1][1].children.append(node)
            stack.append((level, node))

        return root
