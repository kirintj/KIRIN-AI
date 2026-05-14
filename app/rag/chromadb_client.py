import logging
import re
import asyncio
import chromadb
from pathlib import Path
from typing import Optional

from app.rag.embedding import DashScopeEmbeddingFunction
from app.rag.chunker import semantic_chunk

_logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIR = str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db")

CHUNK_SIZE = 500
TOP_K = 5

COLLECTION_NAMES = ("knowledge_base", "resume", "activity-source", "salary", "map-draw")

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
        embed_fn = _get_embedding_function()
        try:
            _collections[name] = client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=embed_fn,
            )
        except ValueError as e:
            if "Embedding function conflict" in str(e):
                _logger.warning("集合 [%s] embedding 函数冲突，删除旧集合并重建: %s", name, e)
                client.delete_collection(name)
                _collections[name] = client.get_or_create_collection(
                    name=name,
                    metadata={"hnsw:space": "cosine"},
                    embedding_function=embed_fn,
                )
            else:
                raise
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
        def _add():
            collection.add(documents=all_chunks, ids=all_ids, metadatas=all_metadatas)
        await asyncio.to_thread(_add)


async def search_chromadb(
    query: str,
    top_k: int = TOP_K,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """从指定集合检索，返回带溯源元数据的结果"""
    collection = _get_collection(collection_name)

    def _query():
        if collection.count() == 0:
            return None
        return collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
        )

    results = await asyncio.to_thread(_query)
    if results is None:
        return [{"content": "知识库暂无数据，请先添加文档。", "source": "", "doc_type": ""}]
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

    def _query():
        if collection.count() == 0:
            return None
        where_filter: dict = {}
        if doc_type:
            where_filter["doc_type"] = doc_type
        if source:
            where_filter["source"] = source
        return collection.query(
            query_texts=[query],
            n_results=min(top_k, collection.count()),
            where=where_filter if where_filter else None,
        )

    results = await asyncio.to_thread(_query)
    if results is None:
        return []
    return _parse_query_results(results, collection_name)


async def hybrid_search(
    query: str,
    top_k: int = TOP_K,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """混合检索：向量检索 + 关键词匹配，RRF 融合排序"""
    collection = _get_collection(collection_name)

    def _search():
        if collection.count() == 0:
            return None, None

        n_retrieve = min(top_k * 3, collection.count())

        vector_results = collection.query(
            query_texts=[query],
            n_results=n_retrieve,
            include=["documents", "metadatas", "distances", "embeddings"],
        )

        keywords = _extract_keywords(query)
        keyword_results = _do_keyword_search(collection, keywords, n_retrieve)

        return vector_results, keyword_results

    vector_results, keyword_results = await asyncio.to_thread(_search)

    if vector_results is None:
        return []

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

    def _delete():
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    await asyncio.to_thread(_delete)
    _collections.pop(collection_name, None)


async def rebuild_all_collections() -> dict:
    """迁移工具：用新 embedding 重建所有集合"""
    client = _get_client()
    embed_fn = _get_embedding_function()

    def _rebuild():
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

    return await asyncio.to_thread(_rebuild)


async def get_collection_stats() -> dict:
    """获取所有集合的文档统计"""
    def _get_stats():
        stats = {}
        for name in COLLECTION_NAMES:
            try:
                collection = _get_collection(name)
                stats[name] = {"count": collection.count()}
            except Exception:
                stats[name] = {"count": 0}
        return stats

    return await asyncio.to_thread(_get_stats)


async def list_documents(
    collection_name: str = "knowledge_base",
    page: int = 1,
    page_size: int = 20,
    doc_type: str = "",
) -> dict:
    """分页浏览指定集合的文档，按 doc_id 聚合"""
    collection = _get_collection(collection_name)

    def _list():
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

    return await asyncio.to_thread(_list)


async def get_document_chunks(
    doc_id: str,
    collection_name: str = "knowledge_base",
) -> list[dict]:
    """获取指定文档的所有分块内容"""
    collection = _get_collection(collection_name)

    def _get_chunks():
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

    return await asyncio.to_thread(_get_chunks)


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
    """从查询中提取关键词（jieba 分词，过滤停用词和短词）"""
    import jieba
    _STOP_WORDS = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个",
        "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
        "自己", "这", "他", "她", "它", "们", "那", "些", "什么", "怎么", "如何", "可以",
        "能", "把", "被", "让", "给", "对", "从", "以", "而", "但", "还", "与", "或",
        "如果", "因为", "所以", "虽然", "但是", "然后", "这个", "那个", "这些", "那些",
        "请", "帮", "想", "需要", "帮我", "一下", "一些",
    }
    words = jieba.lcut(query)
    return [w.strip() for w in words if len(w.strip()) >= 2 and w.strip() not in _STOP_WORDS]


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


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """计算两个向量的余弦相似度"""
    import math
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _rrf_merge(
    vec_results: dict,
    kw_results: dict,
    top_k: int,
    k: int = 60,
    similarity_threshold: float = 0.95,
) -> list[dict]:
    """Reciprocal Rank Fusion 融合向量检索和关键词检索结果，用 embedding 余弦相似度去重"""
    scores: dict[str, float] = {}
    doc_map: dict[str, dict] = {}
    doc_embeddings: dict[str, list[float]] = {}

    vec_docs = vec_results.get("documents", [[]])
    vec_metas = vec_results.get("metadatas", [[]])
    vec_dists = vec_results.get("distances", [[]])
    vec_embeds = vec_results.get("embeddings", [[]])

    for rank in range(len(vec_docs[0])):
        doc = vec_docs[0][rank]
        meta = vec_metas[0][rank] if vec_metas and vec_metas[0] and rank < len(vec_metas[0]) else {}
        dist = vec_dists[0][rank] if vec_dists and vec_dists[0] and rank < len(vec_dists[0]) else 0.0
        embed = vec_embeds[0][rank] if vec_embeds and vec_embeds[0] and rank < len(vec_embeds[0]) else []
        uid = f"vec_{meta.get('doc_id', '')}_{rank}"
        scores[uid] = scores.get(uid, 0) + 1.0 / (k + rank + 1)
        doc_map[uid] = {
            "content": doc,
            "source": meta.get("source", ""),
            "doc_type": meta.get("doc_type", ""),
            "collection": meta.get("collection", ""),
            "distance": dist,
        }
        if embed:
            doc_embeddings[uid] = embed

    kw_docs = kw_results.get("documents", [[]])
    kw_metas = kw_results.get("metadatas", [[]])
    kw_dists = kw_results.get("distances", [[]])

    # 获取关键词结果的 embedding
    kw_embed_fn = _get_embedding_function()
    kw_contents = [kw_docs[0][i] for i in range(len(kw_docs[0]))] if kw_docs and kw_docs[0] else []
    kw_embeds = kw_embed_fn(kw_contents) if kw_contents else []

    for rank in range(len(kw_docs[0])):
        doc = kw_docs[0][rank]
        meta = kw_metas[0][rank] if kw_metas and kw_metas[0] and rank < len(kw_metas[0]) else {}
        dist = kw_dists[0][rank] if kw_dists and kw_dists[0] and rank < len(kw_dists[0]) else 0.0
        kw_embed = kw_embeds[rank] if rank < len(kw_embeds) else []

        # 用 embedding 余弦相似度查找重复文档
        existing_uid = None
        if kw_embed:
            for uid, vec_embed in doc_embeddings.items():
                sim = _cosine_similarity(kw_embed, vec_embed)
                if sim >= similarity_threshold:
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
            if kw_embed:
                doc_embeddings[uid] = kw_embed

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[uid] for uid, _ in ranked[:top_k]]
