from app.rag.ir import TreeNode, Chunk
from app.rag.structural_chunker import chunk_tree


def _make_simple_tree() -> TreeNode:
    """工作经历/阿里巴巴, 工作经历/腾讯, 教育背景"""
    return TreeNode(
        title="简历", level=-1, content="张三\n13800138000", children=[
            TreeNode(title="工作经历", level=1, content="", children=[
                TreeNode(title="阿里巴巴", level=2, content="负责核心系统架构设计\n带领5人团队"),
                TreeNode(title="腾讯", level=2, content="参与微信支付开发"),
            ]),
            TreeNode(title="教育背景", level=1, content="北京大学 计算机科学 本科"),
        ],
    )


def test_chunk_tree_parent_child_structure():
    root = _make_simple_tree()
    chunks = chunk_tree(root, doc_id="doc1", doc_type="resume")
    parents = [c for c in chunks if c.chunk_type == "parent"]
    children = [c for c in chunks if c.chunk_type == "child"]
    assert len(parents) > 0
    assert len(children) > 0
    for child in children:
        assert child.parent_id is not None
        assert child.parent_id in {p.chunk_id for p in parents}


def test_chunk_tree_metadata():
    root = _make_simple_tree()
    chunks = chunk_tree(root, doc_id="doc1", doc_type="resume")
    for c in chunks:
        assert "section_title" in c.metadata
        assert "heading_level" in c.metadata
        assert "section_path" in c.metadata
        assert c.metadata["doc_type"] == "resume"


def test_chunk_tree_section_path():
    root = _make_simple_tree()
    chunks = chunk_tree(root, doc_id="doc1", doc_type="resume")
    child_chunks = [c for c in chunks if c.chunk_type == "child"]
    ali_chunks = [c for c in child_chunks if "阿里巴巴" in c.metadata.get("section_path", "")]
    assert len(ali_chunks) > 0
    assert ali_chunks[0].metadata["section_path"] == "工作经历/阿里巴巴"


def test_chunk_tree_flat_node():
    root = TreeNode(title="文档", level=-1, content="Hello world. This is plain text.")
    chunks = chunk_tree(root, doc_id="doc1", doc_type="plain")
    assert all(c.chunk_type == "parent" for c in chunks)


def test_chunk_tree_empty():
    root = TreeNode(title="空", level=-1)
    chunks = chunk_tree(root, doc_id="doc1", doc_type="plain")
    assert chunks == []


def test_chunk_tree_chunk_ids_unique():
    root = _make_simple_tree()
    chunks = chunk_tree(root, doc_id="doc1", doc_type="resume")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))
