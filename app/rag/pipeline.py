import logging
from dataclasses import dataclass, field

from app.rag.chromadb_client import (
    search_chromadb,
    search_all_collections,
    search_all_collections_hybrid,
    hybrid_search,
    search_with_filter,
    COLLECTION_NAMES,
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


class AdvancedRAGPipeline:
    """高级 RAG 管线：查询改写 → 混合检索 → 重排 → 压缩"""

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()

    async def search(
        self,
        query: str,
        collection_name: str | None = None,
        top_k: int | None = None,
        doc_type: str = "",
        source: str = "",
    ) -> list[dict]:
        """主入口：执行完整高级 RAG 管线"""
        effective_top_k = top_k or self.config.top_k

        # 1. 查询改写
        queries = await self._rewrite_queries(query) if self.config.enable_query_rewrite else [query]

        # 2. 检索
        documents = await self._retrieve(queries, collection_name, effective_top_k, doc_type, source)

        if not documents:
            return []

        # 3. 去重
        documents = self._deduplicate(documents)

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
    ) -> dict:
        """检索 + 生成回答"""
        documents = await self.search(query, collection_name, top_k, doc_type, source)

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
    ) -> list[dict]:
        """多查询检索 + 合并"""
        all_docs: list[dict] = []

        for q in queries:
            if collection_name:
                if doc_type or source:
                    docs = await search_with_filter(q, top_k=top_k, collection_name=collection_name, doc_type=doc_type, source=source)
                elif self.config.enable_hybrid_search:
                    docs = await hybrid_search(q, top_k=top_k, collection_name=collection_name)
                else:
                    docs = await search_chromadb(q, top_k=top_k, collection_name=collection_name)
            else:
                if self.config.enable_hybrid_search:
                    docs = await search_all_collections_hybrid(q, top_k=top_k)
                else:
                    docs = await search_all_collections(q, top_k=top_k)

            all_docs.extend(docs)

        return all_docs

    async def _rerank(self, query: str, documents: list[dict], top_n: int) -> list[dict]:
        """LLM 重排：选出最相关的 top_n 文档"""
        if len(documents) <= top_n:
            return documents

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
            _logger.exception("重排失败，返回原始排序")
            return documents[:top_n]

    async def _compress_context(self, query: str, documents: list[dict]) -> list[dict]:
        """上下文压缩：用 LLM 提取与 query 相关的关键内容"""
        if not documents:
            return documents

        full_context = self._build_context(documents)
        if len(full_context) <= self.config.max_context_chars:
            return documents

        prompt = (
            f"请从以下资料中提取与问题最相关的内容，保留关键信息，去除无关和重复部分，"
            f"总字数不超过{self.config.max_context_chars}字。\n\n"
            f"问题：{query}\n\n资料：\n{full_context}\n\n只输出提取后的内容，不要解释。"
        )
        try:
            compressed = await call_llm(prompt, max_tokens=self.config.max_context_chars, temperature=0.3)
            return [{"content": compressed, "source": "compressed", "doc_type": "", "collection": "", "distance": 0.0}]
        except Exception:
            _logger.exception("上下文压缩失败，返回原始文档")
            return documents

    @staticmethod
    def _deduplicate(documents: list[dict]) -> list[dict]:
        """按内容前 80 字符去重"""
        seen: set[str] = set()
        unique: list[dict] = []
        for d in documents:
            key = d.get("content", "")[:80]
            if key not in seen:
                seen.add(key)
                unique.append(d)
        return unique

    @staticmethod
    def _build_context(documents: list[dict]) -> str:
        """将文档列表拼接为上下文文本"""
        return "\n\n".join(
            f"[资料{i + 1}] {d['content']}" for i, d in enumerate(documents) if d.get("content")
        )
