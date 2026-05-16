from __future__ import annotations

from app.rag.ir import TreeNode, Chunk
from app.rag.chunker import semantic_chunk


def chunk_tree(
    root: TreeNode,
    doc_id: str,
    doc_type: str,
    source: str = "",
    collection_name: str = "",
    user_id: int = 0,
    max_size: int = 500,
    overlap: int = 80,
) -> list[Chunk]:
    """遍历 IR 树，生成 parent-child chunks。"""
    if not root:
        return []

    chunks: list[Chunk] = []
    _counter = {"idx": 0}

    def _next_id(prefix: str) -> str:
        idx = _counter["idx"]
        _counter["idx"] += 1
        return f"{doc_id}_sec_{idx}"

    def _build_section_path(node: TreeNode, parent_path: str = "") -> str:
        if not node.title:
            return parent_path
        return f"{parent_path}/{node.title}" if parent_path else node.title

    def _visit(node: TreeNode, path: str = ""):
        section_path = _build_section_path(node, path)

        if not node.children:
            content = node.content.strip()
            if not content:
                return
            is_structured = node.level > 0
            chunk_type = "child" if is_structured else "parent"
            parent_chunk_id = _find_parent_chunk_id(chunks, section_path, node.level)
            text_chunks = semantic_chunk(content, max_size=max_size, overlap=overlap)
            for text in text_chunks:
                chunk_id = _next_id("c")
                chunks.append(Chunk(
                    text=text,
                    chunk_type=chunk_type,
                    parent_id=parent_chunk_id,
                    chunk_id=chunk_id,
                    metadata={
                        "doc_id": doc_id,
                        "doc_type": doc_type,
                        "source": source,
                        "collection": collection_name,
                        "user_id": user_id,
                        "section_title": node.title,
                        "heading_level": node.level,
                        "section_path": section_path,
                    },
                ))
            return

        # Non-leaf node: generate parent chunk(s) from this node's content
        parent_text = _build_parent_text(node)
        parent_chunk_id = None

        if parent_text.strip():
            parent_chunks_text = semantic_chunk(parent_text, max_size=max_size, overlap=overlap)
            for i, text in enumerate(parent_chunks_text):
                chunk_id = _next_id("p")
                if i == 0:
                    parent_chunk_id = chunk_id
                chunks.append(Chunk(
                    text=text,
                    chunk_type="parent",
                    parent_id=None,
                    chunk_id=chunk_id,
                    metadata={
                        "doc_id": doc_id,
                        "doc_type": doc_type,
                        "source": source,
                        "collection": collection_name,
                        "user_id": user_id,
                        "section_title": node.title,
                        "heading_level": node.level,
                        "section_path": section_path,
                    },
                ))

        # Recurse into children
        for child in node.children:
            _visit_with_parent(child, section_path, parent_chunk_id)

    def _visit_with_parent(node: TreeNode, path: str, parent_chunk_id: str | None):
        section_path = _build_section_path(node, path)

        if not node.children:
            content = node.content.strip()
            if not content:
                return
            text_chunks = semantic_chunk(content, max_size=max_size, overlap=overlap)
            for text in text_chunks:
                chunk_id = _next_id("c")
                chunks.append(Chunk(
                    text=text,
                    chunk_type="child",
                    parent_id=parent_chunk_id,
                    chunk_id=chunk_id,
                    metadata={
                        "doc_id": doc_id,
                        "doc_type": doc_type,
                        "source": source,
                        "collection": collection_name,
                        "user_id": user_id,
                        "section_title": node.title,
                        "heading_level": node.level,
                        "section_path": section_path,
                    },
                ))
            return

        # Non-leaf child: generate parent chunk(s)
        parent_text = _build_parent_text(node)
        node_parent_id = parent_chunk_id

        if parent_text.strip():
            parent_chunks_text = semantic_chunk(parent_text, max_size=max_size, overlap=overlap)
            for i, text in enumerate(parent_chunks_text):
                chunk_id = _next_id("p")
                if i == 0:
                    node_parent_id = chunk_id
                chunks.append(Chunk(
                    text=text,
                    chunk_type="parent",
                    parent_id=parent_chunk_id,
                    chunk_id=chunk_id,
                    metadata={
                        "doc_id": doc_id,
                        "doc_type": doc_type,
                        "source": source,
                        "collection": collection_name,
                        "user_id": user_id,
                        "section_title": node.title,
                        "heading_level": node.level,
                        "section_path": section_path,
                    },
                ))

        for child in node.children:
            _visit_with_parent(child, section_path, node_parent_id)

    # Root's own content (pre-section content) — must be added before children
    # so _find_parent_chunk_id can locate it for top-level leaf sections
    if root.content.strip():
        text_chunks = semantic_chunk(root.content.strip(), max_size=max_size, overlap=overlap)
        for text in text_chunks:
            chunk_id = _next_id("p")
            chunks.append(Chunk(
                text=text,
                chunk_type="parent",
                parent_id=None,
                chunk_id=chunk_id,
                metadata={
                    "doc_id": doc_id,
                    "doc_type": doc_type,
                    "source": source,
                    "collection": collection_name,
                    "user_id": user_id,
                    "section_title": root.title,
                    "heading_level": root.level,
                    "section_path": "",
                },
            ))

    # Start DFS from root
    for child in root.children:
        _visit(child, "")

    return chunks


def _build_parent_text(node: TreeNode) -> str:
    """构建 parent chunk 文本：title + content + 子节点标题列表。"""
    parts: list[str] = []
    if node.title:
        parts.append(node.title)
    if node.content and node.content.strip():
        parts.append(node.content.strip())
    for child in node.children:
        if child.title:
            parts.append(f"- {child.title}")
    return "\n".join(parts)


def _find_parent_chunk_id(chunks: list[Chunk], section_path: str, level: int) -> str | None:
    """查找最近的 parent chunk id，用于 leaf 节点的 parent_id。"""
    root_fallback = None
    for chunk in reversed(chunks):
        if chunk.chunk_type == "parent":
            parent_path = chunk.metadata.get("section_path", "")
            if parent_path and section_path.startswith(parent_path):
                return chunk.chunk_id
            if not parent_path and root_fallback is None:
                root_fallback = chunk.chunk_id
    return root_fallback
