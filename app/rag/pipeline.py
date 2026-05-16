import asyncio
import logging
import math
from dataclasses import dataclass, field

from app.tools.base import build_rag_context
from app.rag.chromadb_client import (
    search_chromadb,
    search_all_collections,
    search_all_collections_hybrid,
    hybrid_search,
    search_with_filter,
    _get_embedding_function,
)
from app.utils.chat import call_llm
from app.settings import settings

_logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    enable_query_rewrite: bool = field(default_factory=lambda: settings.RAG_ENABLE_QUERY_REWRITE)
    enable_hybrid_search: bool = field(default_factory=lambda: settings.RAG_ENABLE_HYBRID_SEARCH)
    enable_rerank: bool = field(default_factory=lambda: settings.RAG_ENABLE_RERANK)
    enable_context_compress: bool = field(default_factory=lambda: settings.RAG_ENABLE_CONTEXT_COMPRESS)
    top_k: int = 5
    rerank_top_n: int = 3
    max_context_chars: int = 6000
    rerank_api_key: str = ""
    rerank_base_url: str = ""
    rerank_model: str = ""


async def load_pipeline_config_from_db() -> PipelineConfig:
    """从数据库加载 RAG 管线配置，带 5 秒 TTL 缓存"""
    from app.services.config import get_cached_ai_config

    cfg = await get_cached_ai_config()
    return PipelineConfig(
        enable_query_rewrite=cfg.get("rag_enable_query_rewrite", "true") == "true",
        enable_hybrid_search=cfg.get("rag_enable_hybrid_search", "true") == "true",
        enable_rerank=cfg.get("rag_enable_rerank", "true") == "true",
        enable_context_compress=cfg.get("rag_enable_context_compress", "false") == "true",
        rerank_api_key=cfg.get("rerank_api_key", ""),
        rerank_base_url=cfg.get("rerank_base_url", ""),
        rerank_model=cfg.get("rerank_model", ""),
    )


class AdvancedRAGPipeline:
    """高级 RAG 管线：查询改写 → 混合检索 → 重排 → 压缩"""

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config
        self._config_explicit = config is not None

    async def search(
        self,
        query: str,
        collection_name: str | None = None,
        top_k: int | None = None,
        doc_type: str = "",
        source: str = "",
        user_id: int = 0,
    ) -> list[dict]:
        """主入口：执行完整高级 RAG 管线"""
        if not self._config_explicit:
            self.config = await load_pipeline_config_from_db()

        effective_top_k = top_k or self.config.top_k

        # 1. 查询改写
        queries = await self._rewrite_queries(query) if self.config.enable_query_rewrite else [query]

        # 2. 检索
        documents = await self._retrieve(queries, collection_name, effective_top_k, doc_type, source, user_id=user_id)

        if not documents:
            return []

        # 2.5 补充 parent 上下文
        documents = await self._enrich_with_parent_context(documents, collection_name, user_id)

        # 3. 去重
        documents = await self._deduplicate(documents)

        # 4. 重排
        if self.config.enable_rerank and len(documents) > self.config.rerank_top_n:
            documents = await self._rerank(query, documents, self.config.rerank_top_n)

        # 5. 上下文压缩
        if self.config.enable_context_compress:
            documents = await self._compress_context(query, documents)

        return documents

    async def search_and_generate(
        self,
        query: str,
        collection_name: str | None = None,
        top_k: int | None = None,
        doc_type: str = "",
        source: str = "",
        user_id: int = 0,
    ) -> dict:
        """检索 + 生成回答"""
        documents = await self.search(query, collection_name, top_k, doc_type, source, user_id=user_id)

        if not documents:
            return {"answer": "未检索到相关文档，请先添加知识库文档。", "sources": [], "documents": []}

        context = self._build_context(documents)
        sources = list(set(d.get("source", "") for d in documents if d.get("source")))

        prompt = (
            f"基于以下检索到的文档内容回答问题。要求内容贴合文档、个性化强、逻辑清晰。"
            f"如果内容中没有相关信息，请说明无法回答。\n\n"
            f"参考资料：\n{context}\n\n问题：{query}"
        )
        answer = await call_llm(prompt)

        return {
            "answer": answer,
            "sources": sources,
            "documents": documents,
        }

    async def _rewrite_queries(self, original_query: str) -> list[str]:
        """用 LLM 改写查询，生成多角度检索 query"""
        prompt = (
            f"你是一个查询改写专家。将用户的原始问题改写为 2-3 个更精确的检索查询，"
            f"每个一行，侧重不同角度（如关键词提取、同义替换、上下文补充）。\n"
            f"只输出改写后的查询，不要编号，不要解释。\n\n"
            f"原始问题：{original_query}"
        )
        try:
            result = await call_llm(prompt, max_tokens=200, temperature=0.3)
            rewritten = [q.strip() for q in result.strip().split("\n") if q.strip()]
            rewritten.insert(0, original_query)
            return rewritten[:4]
        except Exception:
            _logger.exception("查询改写失败，使用原始查询")
            return [original_query]

    async def _retrieve(
        self,
        queries: list[str],
        collection_name: str | None,
        top_k: int,
        doc_type: str,
        source: str,
        user_id: int = 0,
    ) -> list[dict]:
        """多查询检索 + 合并"""
        all_docs: list[dict] = []

        for q in queries:
            if collection_name:
                if doc_type or source:
                    docs = await search_with_filter(q, top_k=top_k, collection_name=collection_name, doc_type=doc_type, source=source, user_id=user_id)
                elif self.config.enable_hybrid_search:
                    docs = await hybrid_search(q, top_k=top_k, collection_name=collection_name, user_id=user_id)
                else:
                    docs = await search_chromadb(q, top_k=top_k, collection_name=collection_name, user_id=user_id)
            else:
                if self.config.enable_hybrid_search:
                    docs = await search_all_collections_hybrid(q, top_k=top_k, user_id=user_id)
                else:
                    docs = await search_all_collections(q, top_k=top_k, user_id=user_id)

            all_docs.extend(docs)

        return all_docs

    async def _enrich_with_parent_context(
        self, documents: list[dict], collection_name: str, user_id: int
    ) -> list[dict]:
        """对检索结果补充 parent 上下文"""
        parent_ids = {d.get("parent_id") for d in documents if d.get("parent_id")}
        if not parent_ids:
            return documents

        from app.rag.chromadb_client import fetch_parent_chunks

        parent_chunks = await fetch_parent_chunks(parent_ids, collection_name, user_id)
        parent_map = {p["chunk_id"]: p for p in parent_chunks}

        for doc in documents:
            pid = doc.get("parent_id")
            if pid and pid in parent_map:
                doc["parent_content"] = parent_map[pid].get("content", "")
                doc["section_title"] = parent_map[pid].get("section_title", "")
                doc["section_path"] = parent_map[pid].get("section_path", "")

        return documents

    async def _rerank(self, query: str, documents: list[dict], top_n: int) -> list[dict]:
        """DashScope gte-rerank 模型重排"""
        if len(documents) <= top_n:
            return documents

        try:
            import httpx

            api_key = self.config.rerank_api_key or settings.RERANK_API_KEY
            if not api_key:
                _logger.warning("RERANK_API_KEY 未配置，使用 LLM 重排")
                return await self._rerank_with_llm(query, documents, top_n)

            base_url = self.config.rerank_base_url or settings.RERANK_BASE_URL
            model = self.config.rerank_model or settings.RERANK_MODEL
            docs_text = [d["content"][:500] for d in documents]

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    base_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "input": {"query": query, "documents": docs_text},
                        "parameters": {"top_n": top_n, "return_documents": False},
                    },
                )

            if response.status_code == 200:
                result = response.json()
                indices = [item["index"] for item in result["output"]["results"]]
                return [documents[i] for i in indices]
            else:
                _logger.warning("gte-rerank 调用失败: %s, 回退 LLM 重排", response.status_code)
                return await self._rerank_with_llm(query, documents, top_n)

        except Exception:
            _logger.exception("重排失败，回退 LLM 重排")
            return await self._rerank_with_llm(query, documents, top_n)

    async def _rerank_with_llm(self, query: str, documents: list[dict], top_n: int) -> list[dict]:
        """LLM 重排：选出最相关的 top_n 文档"""
        doc_list = "\n".join(
            f"[{i + 1}] {d['content'][:200]}" for i, d in enumerate(documents)
        )
        prompt = (
            f"根据用户问题，从以下文档中选出最相关的 {top_n} 个，按相关性从高到低输出序号，每行一个数字。\n\n"
            f"用户问题：{query}\n\n文档：\n{doc_list}\n\n只输出序号，不要解释。"
        )
        try:
            result = await call_llm(prompt, max_tokens=50, temperature=0.1)
            selected_indices: list[int] = []
            for line in result.strip().split("\n"):
                line = line.strip().strip("[]()、，,")
                if line.isdigit():
                    idx = int(line) - 1
                    if 0 <= idx < len(documents) and idx not in selected_indices:
                        selected_indices.append(idx)

            if not selected_indices:
                return documents[:top_n]

            return [documents[i] for i in selected_indices[:top_n]]
        except Exception:
            _logger.exception("LLM 重排失败，返回原始排序")
            return documents[:top_n]

    async def _compress_context(self, query: str, documents: list[dict]) -> list[dict]:
        """上下文压缩：用 LLM 提取与 query 相关的关键内容，保留原始来源"""
        if not documents:
            return documents

        full_context = self._build_context(documents)
        if len(full_context) <= self.config.max_context_chars:
            return documents

        # 收集所有原始来源
        sources = list(set(d.get("source", "") for d in documents if d.get("source")))
        doc_types = list(set(d.get("doc_type", "") for d in documents if d.get("doc_type")))
        collections = list(set(d.get("collection", "") for d in documents if d.get("collection")))

        prompt = (
            f"请从以下资料中提取与问题最相关的内容，保留关键信息，去除无关和重复部分，"
            f"总字数不超过{self.config.max_context_chars}字。\n\n"
            f"问题：{query}\n\n资料：\n{full_context}\n\n只输出提取后的内容，不要解释。"
        )
        try:
            compressed = await call_llm(prompt, max_tokens=self.config.max_context_chars, temperature=0.3)
            return [{
                "content": compressed,
                "source": ", ".join(sources) if sources else "",
                "doc_type": ", ".join(doc_types) if doc_types else "",
                "collection": ", ".join(collections) if collections else "",
                "distance": 0.0,
                "is_compressed": True,
                "source_count": len(sources),
            }]
        except Exception:
            _logger.exception("上下文压缩失败，返回原始文档")
            return documents

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """计算两个向量的余弦相似度"""
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    @staticmethod
    async def _deduplicate(documents: list[dict], similarity_threshold: float = 0.95) -> list[dict]:
        """用 embedding 余弦相似度去重，阈值 0.95"""
        if not documents:
            return documents

        embed_fn = _get_embedding_function()
        contents = [d.get("content", "") for d in documents]
        embeddings = await asyncio.to_thread(embed_fn, contents)

        unique_indices: list[int] = []
        unique_embeddings: list[list[float]] = []

        for i, embed in enumerate(embeddings):
            is_duplicate = False
            for unique_embed in unique_embeddings:
                sim = AdvancedRAGPipeline._cosine_similarity(embed, unique_embed)
                if sim >= similarity_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_indices.append(i)
                unique_embeddings.append(embed)

        return [documents[i] for i in unique_indices]

    @staticmethod
    def _build_context(documents: list[dict]) -> str:
        """将文档列表拼接为上下文文本"""
        context, _ = build_rag_context(documents)
        return context
