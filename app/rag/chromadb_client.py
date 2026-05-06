import logging
import re
import chromadb
from pathlib import Path
from typing import Optional

from app.rag.embedding import DashScopeEmbeddingFunction
from app.rag.chunker import semantic_chunk

_logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db")

CHUNK_SIZE = 500
TOP_K = 5

COLLECTION_NAMES = ("knowledge_base", "resume", "interview", "salary", "guide")

_client: Optional[chromadb.ClientAPI] = None
_collections: dict[str, chromadb.Collection] = {}
_embedding_fn: Optional[DashScopeEmbeddingFunction] = None


def _get_embedding_function() -> DashScopeEmbeddingFunction:
    global _embedding_fn
    if _embedding_fn is None:
        _embedding_fn = DashScopeEmbeddingFunction()
    return _embedding_fn


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
            embedding_function=_get_embedding_function(),
        )
    return _collections[name]


async def add_documents(
    documents: list[str],
    doc_ids: list[str] | None = None,
    collection_name: str = "knowledge_base",
    source: str = "",
    doc_type: str = "",
):
    """将文档语义分块后存入指定集合，携带溯源元数据"""
    collection = _get_collection(collection_name)
    all_chunks: list[str] = []
    all_ids: list[str] = []
    all_metadatas: list[dict] = []

    for idx, doc in enumerate(documents):
        chunks = semantic_chunk(doc, max_size=CHUNK_SIZE)
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
    return _parse_query_results(results, collection_name)


async def search_with_filter(
    query: str,
    top_k: int = TOP_K,
    collection_name: str = "knowledge_base",
    doc_type: str = "",
    source: str = "",
) -> list[dict]:
    """带元数据过滤的检索"""
    collection = _get_collection(collection_name)
    if collection.count() == 0:
        return []

    where_filter: dict = {}
    if doc_type:
        where_filter["doc_type"] = doc_type
    if source:
        where_filter["source"] = source

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        where=where_filter if where_filter else None,
    )
    return _parse_query_results(results, collection_name)


async def hybrid_search(
    query: str,
    top_k: int = TOP_K,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """混合检索：向量检索 + 关键词匹配，RRF 融合排序"""
    collection = _get_collection(collection_name)
    if collection.count() == 0:
        return []

    n_retrieve = min(top_k * 3, collection.count())

    vector_results = collection.query(
        query_texts=[query],
        n_results=n_retrieve,
    )

    keywords = _extract_keywords(query)
    keyword_results = _do_keyword_search(collection, keywords, n_retrieve)

    if not keyword_results:
        return _parse_query_results(vector_results, collection_name)

    merged = _rrf_merge(vector_results, keyword_results, top_k)
    return merged


async def search_all_collections(query: str, top_k: int = 3) -> list[dict]:
    """跨所有集合检索，合并结果按距离排序"""
    all_results: list[dict] = []
    for name in COLLECTION_NAMES:
        try:
            results = await search_chromadb(query, top_k=top_k, collection_name=name)
            all_results.extend(results)
        except Exception:
            continue
    all_results.sort(key=lambda x: x.get("distance", 1.0))
    return all_results[: top_k * 2]


async def search_all_collections_hybrid(query: str, top_k: int = 3) -> list[dict]:
    """跨所有集合混合检索"""
    all_results: list[dict] = []
    for name in COLLECTION_NAMES:
        try:
            results = await hybrid_search(query, top_k=top_k, collection_name=name)
            all_results.extend(results)
        except Exception:
            continue
    all_results.sort(key=lambda x: x.get("distance", 1.0))
    return all_results[: top_k * 2]


async def delete_all_documents(collection_name: str = "knowledge_base"):
    """清空指定集合"""
    client = _get_client()
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    _collections.pop(collection_name, None)


async def rebuild_all_collections() -> dict:
    """迁移工具：用新 embedding 重建所有集合"""
    client = _get_client()
    embed_fn = _get_embedding_function()
    migrated: dict[str, int] = {}

    for name in COLLECTION_NAMES:
        try:
            old_collection = client.get_collection(name=name)
            if old_collection.count() == 0:
                migrated[name] = 0
                continue

            all_data = old_collection.get(include=["documents", "metadatas"])
            raw_docs = all_data.get("documents", [])
            raw_metas = all_data.get("metadatas", [])

            doc_groups: dict[str, dict] = {}
            for i, content in enumerate(raw_docs):
                meta = raw_metas[i] if i < len(raw_metas) and raw_metas[i] else {}
                doc_id = meta.get("doc_id", f"doc_{i}")
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = {
                        "chunks": [],
                        "source": meta.get("source", ""),
                        "doc_type": meta.get("doc_type", ""),
                    }
                doc_groups[doc_id]["chunks"].append(content)

            client.delete_collection(name)
            _collections.pop(name, None)

            new_collection = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=embed_fn,
            )
            _collections[name] = new_collection

            count = 0
            for doc_id, group in doc_groups.items():
                full_text = "\n\n".join(group["chunks"])
                chunks = semantic_chunk(full_text, max_size=CHUNK_SIZE)
                chunk_ids = [f"{doc_id}_chunk_{j}" for j in range(len(chunks))]
                metas = [
                    {
                        "doc_id": doc_id,
                        "chunk_index": j,
                        "source": group["source"],
                        "doc_type": group["doc_type"],
                        "collection": name,
                    }
                    for j in range(len(chunks))
                ]
                if chunks:
                    new_collection.add(documents=chunks, ids=chunk_ids, metadatas=metas)
                    count += len(chunks)

            migrated[name] = count
            _logger.info("集合 [%s] 迁移完成, %d 个分块", name, count)

        except Exception:
            _logger.exception("集合 [%s] 迁移失败", name)
            migrated[name] = -1

    return migrated


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
        meta = raw_metas[i] if i < len(raw_metas) and raw_metas[i] else {}
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
        meta = raw_metas[i] if i < len(raw_metas) and raw_metas[i] else {}
        chunks.append({
            "chunk_index": meta.get("chunk_index", i),
            "content": content,
            "source": meta.get("source", ""),
            "doc_type": meta.get("doc_type", ""),
        })

    chunks.sort(key=lambda x: x["chunk_index"])
    return chunks


def _parse_query_results(results: dict, collection_name: str) -> list[dict]:
    """解析 ChromaDB query 返回值"""
    documents = results.get("documents", [[]])
    metadatas = results.get("metadatas", [[]])
    distances = results.get("distances", [[]])

    if not documents or not documents[0]:
        return []

    items: list[dict] = []
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


def _extract_keywords(query: str) -> list[str]:
    """从查询中提取关键词（简单分词：按标点和空格切分，过滤短词）"""
    segments = re.split(r"[，。！？、；：\s]+", query)
    return [s.strip() for s in segments if len(s.strip()) >= 2]


def _do_keyword_search(
    collection: chromadb.Collection,
    keywords: list[str],
    n_results: int,
) -> dict | None:
    """关键词精确匹配检索"""
    if not keywords:
        return None

    for kw in keywords[:3]:
        try:
            results = collection.query(
                query_texts=[""],
                n_results=n_results,
                where_document={"$contains": kw},
            )
            if results and results.get("documents") and results["documents"][0]:
                return results
        except Exception:
            continue
    return None


def _rrf_merge(
    vec_results: dict,
    kw_results: dict,
    top_k: int,
    k: int = 60,
) -> list[dict]:
    """Reciprocal Rank Fusion 融合向量检索和关键词检索结果"""
    scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}

    vec_docs = vec_results.get("documents", [[]])
    vec_metas = vec_results.get("metadatas", [[]])
    vec_dists = vec_results.get("distances", [[]])

    for rank in range(len(vec_docs[0])):
        doc = vec_docs[0][rank]
        meta = vec_metas[0][rank] if vec_metas and vec_metas[0] and rank < len(vec_metas[0]) else {}
        dist = vec_dists[0][rank] if vec_dists and vec_dists[0] and rank < len(vec_dists[0]) else 0.0
        uid = f"vec_{meta.get('doc_id', '')}_{rank}"
        scores[uid] = scores.get(uid, 0) + 1.0 / (k + rank + 1)
        doc_map[uid] = {
            "content": doc,
            "source": meta.get("source", ""),
            "doc_type": meta.get("doc_type", ""),
            "collection": meta.get("collection", ""),
            "distance": dist,
        }

    kw_docs = kw_results.get("documents", [[]])
    kw_metas = kw_results.get("metadatas", [[]])
    kw_dists = kw_results.get("distances", [[]])

    for rank in range(len(kw_docs[0])):
        doc = kw_docs[0][rank]
        meta = kw_metas[0][rank] if kw_metas and kw_metas[0] and rank < len(kw_metas[0]) else {}
        dist = kw_dists[0][rank] if kw_dists and kw_dists[0] and rank < len(kw_dists[0]) else 0.0
        content_key = doc[:80]
        existing_uid = None
        for uid, info in doc_map.items():
            if info["content"][:80] == content_key:
                existing_uid = uid
                break

        if existing_uid:
            scores[existing_uid] += 1.0 / (k + rank + 1)
        else:
            uid = f"kw_{meta.get('doc_id', '')}_{rank}"
            scores[uid] = scores.get(uid, 0) + 1.0 / (k + rank + 1)
            doc_map[uid] = {
                "content": doc,
                "source": meta.get("source", ""),
                "doc_type": meta.get("doc_type", ""),
                "collection": meta.get("collection", ""),
                "distance": dist,
            }

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[uid] for uid, _ in ranked[:top_k]]
