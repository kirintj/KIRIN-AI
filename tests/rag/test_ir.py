from app.rag.ir import TreeNode, Chunk


def test_tree_node_defaults():
    node = TreeNode(title="Test", level=1)
    assert node.content == ""
    assert node.children == []
    assert node.metadata == {}


def test_tree_node_with_children():
    child = TreeNode(title="Child", level=2, content="child content")
    parent = TreeNode(title="Parent", level=1, content="parent content", children=[child])
    assert len(parent.children) == 1
    assert parent.children[0].title == "Child"


def test_chunk_defaults():
    chunk = Chunk(text="hello", chunk_type="parent")
    assert chunk.parent_id is None
    assert chunk.chunk_id == ""
    assert chunk.metadata == {}


def test_chunk_with_parent():
    chunk = Chunk(text="child text", chunk_type="child", parent_id="parent_001", chunk_id="child_001")
    assert chunk.parent_id == "parent_001"
    assert chunk.chunk_type == "child"
