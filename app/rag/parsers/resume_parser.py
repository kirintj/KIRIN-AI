from __future__ import annotations

import re

from app.rag.ir import TreeNode
from app.rag.parsers.base import BaseParser

_RESUME_KEYWORDS = (
    "个人简介", "基本信息", "基本资料", "求职意向",
    "工作经历", "工作经验", "项目经历", "项目经验", "实习经历",
    "教育背景", "教育经历", "教育信息",
    "专业技能", "技能特长", "技能清单",
    "自我评价", "个人总结", "荣誉奖项", "证书资质", "兴趣爱好",
)

_SECTION_RE = re.compile(
    r"^[ \t]*(" + "|".join(re.escape(k) for k in _RESUME_KEYWORDS) + r")[ \t:：]?[ \t]*$",
)
_LIST_RE = re.compile(r"^[ \t]*[-*]\s+|^[ \t]*\d+[\.\)]\s+")


class ResumeParser(BaseParser):
    """按简历分节关键词解析为树结构。"""

    def parse(self, text: str, title: str = "") -> TreeNode:
        root = TreeNode(title=title or "简历", level=-1)
        if not text or not text.strip():
            return root

        lines = text.split("\n")
        current_section: TreeNode | None = None
        pre_section_lines: list[str] = []
        current_item_lines: list[str] = []

        def _flush_item():
            if current_item_lines and current_section is not None:
                content = "\n".join(current_item_lines).strip()
                if content:
                    item_node = TreeNode(
                        title=content[:50],
                        level=2,
                        content=content,
                    )
                    current_section.children.append(item_node)
                current_item_lines.clear()

        for line in lines:
            m = _SECTION_RE.match(line.strip())
            if m:
                _flush_item()
                if current_section is None and pre_section_lines:
                    root.content = "\n".join(pre_section_lines).strip()
                    pre_section_lines.clear()

                section_title = m.group(1).strip()
                current_section = TreeNode(title=section_title, level=1)
                root.children.append(current_section)
            elif current_section is not None:
                if _LIST_RE.match(line.strip()):
                    _flush_item()
                    current_item_lines.append(line.strip())
                else:
                    current_item_lines.append(line)
            else:
                pre_section_lines.append(line)

        _flush_item()

        if current_section is None and pre_section_lines:
            root.content = "\n".join(pre_section_lines).strip()

        return root
