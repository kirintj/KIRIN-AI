from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TreeNode:
    """文档结构树节点"""

    title: str
    level: int
    content: str = ""
    children: list[TreeNode] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class Chunk:
    """分块输出"""

    text: str
    chunk_type: str  # "parent" | "child"
    parent_id: str | None = None
    chunk_id: str = ""
    metadata: dict = field(default_factory=dict)
