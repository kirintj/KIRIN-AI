from __future__ import annotations

import re

from app.rag.ir import TreeNode
from app.rag.parsers.base import BaseParser
from app.rag.parsers.plain_parser import PlainParser
from app.rag.parsers.resume_parser import ResumeParser
from app.rag.doc_type_detector import detect_doc_type

_NUMBERED_RE = re.compile(r"^(\d+)[\.\、]\s*(.+)")


class PdfParser(BaseParser):
    """PDF 启发式解析：尝试编号标题、简历关键词，否则回退 plain。"""

    def __init__(self):
        self._resume_parser = ResumeParser()
        self._plain_parser = PlainParser()

    def parse(self, text: str, title: str = "") -> TreeNode:
        if not text or not text.strip():
            return TreeNode(title=title or "PDF文档", level=-1)

        # Try resume detection first
        if detect_doc_type(text) == "resume":
            return self._resume_parser.parse(text, title)

        # Try numbered section headings
        lines = text.split("\n")
        sections: list[tuple[str, list[str]]] = []
        current_title = ""
        current_lines: list[str] = []

        for line in lines:
            m = _NUMBERED_RE.match(line.strip())
            if m:
                if current_title or current_lines:
                    sections.append((current_title, list(current_lines)))
                    current_lines.clear()
                current_title = m.group(2).strip() if m.group(2).strip() else m.group(1)
            else:
                current_lines.append(line)

        if current_title or current_lines:
            sections.append((current_title, list(current_lines)))

        # If we found at least 2 numbered sections, use them
        titled_sections = [(t, l) for t, l in sections if t]
        if len(titled_sections) >= 2:
            root = TreeNode(title=title or "PDF文档", level=-1)
            pre_content = sections[0][1] if sections and not sections[0][0] else []
            if pre_content:
                root.content = "\n".join(pre_content).strip()

            for sec_title, sec_lines in titled_sections:
                content = "\n".join(sec_lines).strip()
                node = TreeNode(title=sec_title, level=1, content=content)
                root.children.append(node)
            return root

        # Fallback to plain
        return self._plain_parser.parse(text, title)
