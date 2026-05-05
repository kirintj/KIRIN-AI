import chromadb
from pathlib import Path
from typing import Optional

CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db")

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 5

COLLECTION_NAMES = ("knowledge_base", "resume", "interview", "salary", "guide")

_client: Optional[chromadb.ClientAPI] = None
_collections: dict[str, chromadb.Collection] = {}


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def _get_collection(name: str = "knowledge_base") -> chromadb.Collection:
    if name not in _collections:
        client = _get_client()
        _collections[name] = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
    return _collections[name]


def _split_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


async def add_documents(
    documents: list[str],
    doc_ids: list[str] | None = None,
    collection_name: str = "knowledge_base",
    source: str = "",
    doc_type: str = "",
):
    """将文档分块后存入指定集合，携带溯源元数据"""
    collection = _get_collection(collection_name)
    all_chunks = []
    all_ids = []
    all_metadatas = []

    for idx, doc in enumerate(documents):
        chunks = _split_text(doc)
        doc_id = doc_ids[idx] if doc_ids else f"doc_{idx}"
        for chunk_idx, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{doc_id}_chunk_{chunk_idx}")
            all_metadatas.append({
                "doc_id": doc_id,
                "chunk_index": chunk_idx,
                "source": source or doc_id,
                "doc_type": doc_type,
                "collection": collection_name,
            })

    if all_chunks:
        collection.add(
            documents=all_chunks,
            ids=all_ids,
            metadatas=all_metadatas,
        )


async def search_chromadb(
    query: str,
    top_k: int = TOP_K,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """从指定集合检索，返回带溯源元数据的结果"""
    collection = _get_collection(collection_name)
    if collection.count() == 0:
        return [{"content": "知识库暂无数据，请先添加文档。", "source": "", "doc_type": ""}]

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
    )

    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])

    if not documents or not documents[0]:
        return []

    items = []
    for i, doc in enumerate(documents[0]):
        meta = metadatas[0][i] if metadatas and metadatas[0] and i < len(metadatas[0]) else {}
        distance = distances[0][i] if distances and distances[0] and i < len(distances[0]) else 0.0
        items.append({
            "content": doc,
            "source": meta.get("source", ""),
            "doc_type": meta.get("doc_type", ""),
            "collection": meta.get("collection", collection_name),
            "distance": distance,
        })
    return items


async def search_all_collections(query: str, top_k: int = 3) -> list[dict]:
    """跨所有集合检索，合并结果按距离排序"""
    all_results = []
    for name in COLLECTION_NAMES:
        try:
            results = await search_chromadb(query, top_k=top_k, collection_name=name)
            all_results.extend(results)
        except Exception:
            continue
    all_results.sort(key=lambda x: x.get("distance", 1.0))
    return all_results[:top_k * 2]


async def delete_all_documents(collection_name: str = "knowledge_base"):
    """清空指定集合"""
    client = _get_client()
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    _collections.pop(collection_name, None)


async def get_collection_stats() -> dict:
    """获取所有集合的文档统计"""
    stats = {}
    for name in COLLECTION_NAMES:
        try:
            collection = _get_collection(name)
            stats[name] = {"count": collection.count()}
        except Exception:
            stats[name] = {"count": 0}
    return stats


async def list_documents(
    collection_name: str = "knowledge_base",
    page: int = 1,
    page_size: int = 20,
    doc_type: str = "",
) -> dict:
    """分页浏览指定集合的文档，按 doc_id 聚合"""
    collection = _get_collection(collection_name)
    total = collection.count()
    if total == 0:
        return {"total": 0, "page": page, "page_size": page_size, "documents": []}

    results = collection.get(include=["documents", "metadatas"])
    raw_docs = results.get("documents", [])
    raw_metas = results.get("metadatas", [])
    raw_ids = results.get("ids", [])

    doc_groups: dict[str, dict] = {}
    for i, chunk_id in enumerate(raw_ids):
        meta = raw_metas[i] if i < len(raw_metas) else {}
        doc_id = meta.get("doc_id", chunk_id)
        dtype = meta.get("doc_type", "")
        source = meta.get("source", "")

        if doc_type and dtype != doc_type:
            continue

        if doc_id not in doc_groups:
            doc_groups[doc_id] = {
                "doc_id": doc_id,
                "source": source,
                "doc_type": dtype,
                "chunk_count": 0,
                "preview": "",
            }
        doc_groups[doc_id]["chunk_count"] += 1
        content = raw_docs[i] if i < len(raw_docs) else ""
        if not doc_groups[doc_id]["preview"] and content:
            doc_groups[doc_id]["preview"] = content[:200]

    all_docs = list(doc_groups.values())
    all_docs.sort(key=lambda x: x.get("doc_id", ""))

    start = (page - 1) * page_size
    end = start + page_size
    paged = all_docs[start:end]

    return {
        "total": len(all_docs),
        "page": page,
        "page_size": page_size,
        "documents": paged,
    }


async def get_document_chunks(
    doc_id: str,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """获取指定文档的所有分块内容"""
    collection = _get_collection(collection_name)

    results = collection.get(
        where={"doc_id": doc_id},
        include=["documents", "metadatas"],
    )

    chunks = []
    raw_docs = results.get("documents", [])
    raw_metas = results.get("metadatas", [])
    for i, content in enumerate(raw_docs):
        meta = raw_metas[i] if i < len(raw_metas) else {}
        chunks.append({
            "chunk_index": meta.get("chunk_index", i),
            "content": content,
            "source": meta.get("source", ""),
            "doc_type": meta.get("doc_type", ""),
        })

    chunks.sort(key=lambda x: x["chunk_index"])
    return chunks
