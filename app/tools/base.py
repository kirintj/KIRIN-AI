import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.utils.chat import call_llm


def build_rag_context(docs: list[dict], empty_msg: str = "暂无相关文档。") -> tuple[str, list[str]]:
    """将 RAG 检索结果格式化为上下文文本和来源列表。"""
    if not docs or (len(docs) == 1 and docs[0].get("source") == ""):
        return empty_msg, []
    context_parts = [f"[文档{i+1}] {d['content']}" for i, d in enumerate(docs) if d.get("content")]
    sources = list(set(d.get("source", "") for d in docs if d.get("source")))
    return "\n\n".join(context_parts), sources


def ensure_user_dir(base_dir: Path, user_id: str) -> Path:
    """Create and return a user-specific directory under base_dir."""
    user_dir = base_dir / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


class BaseTool(ABC):
    """Agent 工具基类，提供统一接口和 JSON 清理工具方法。"""

    name: str = ""

    @abstractmethod
    async def run(self, query: str = "", **kwargs: Any) -> str:
        raise NotImplementedError

    @staticmethod
    def clean_json(text: str) -> str:
        """去除 LLM 返回文本中的 markdown 代码块标记，返回纯 JSON 字符串。"""
        text = text.strip()
        for prefix in ("```json", "```"):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

    @staticmethod
    def parse_json(text: str) -> dict | None:
        """解析 LLM 返回的 JSON 文本，失败返回 None。"""
        try:
            return json.loads(BaseTool.clean_json(text))
        except (json.JSONDecodeError, AttributeError):
            return None

    @staticmethod
    def build_rag_context(docs: list[dict], empty_msg: str = "暂无相关文档。") -> tuple[str, list[str]]:
        """代理到模块级 build_rag_context。"""
        return build_rag_context(docs, empty_msg)


class RAGToolBase(BaseTool):
    """RAG 工具基类，封装管线初始化、检索、生成流程。

    子类只需定义：
    - COLLECTION_NAME: 目标集合名
    - PROMPT_TEMPLATE: 含 {doc_context} 的 prompt 模板
    - build_search_query(): 从 kwargs 构造检索 query
    - build_prompt_vars(): 从 kwargs 构造 prompt 模板变量
    - empty_msg: 无文档时的默认提示
    """

    COLLECTION_NAME: str = ""
    PROMPT_TEMPLATE: str = ""
    empty_msg: str = "暂无相关文档。"
    max_tokens: int = 3000
    temperature: float = 0.7

    def __init__(self):
        from app.rag.pipeline import AdvancedRAGPipeline
        self._pipeline = AdvancedRAGPipeline()

    @abstractmethod
    def build_search_query(self, query: str, **kwargs) -> str:
        """从用户输入构造检索 query"""

    @abstractmethod
    def build_prompt_vars(self, query: str, **kwargs) -> dict:
        """从 kwargs 构造 prompt 模板变量（不含 doc_context）"""

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = int(kwargs.get("user_id", 0))
        search_query = self.build_search_query(query, **kwargs)
        docs = await self._pipeline.search(search_query, collection_name=self.COLLECTION_NAME, user_id=user_id)

        doc_context, sources = self.build_rag_context(docs, self.empty_msg)

        prompt_vars = self.build_prompt_vars(query, **kwargs)
        prompt_vars["doc_context"] = doc_context
        prompt = self.PROMPT_TEMPLATE.format(**prompt_vars)

        answer = await call_llm(prompt, max_tokens=self.max_tokens, temperature=self.temperature)

        if sources:
            answer += f"\n\n参考文档来源：{', '.join(sources)}"
        return answer
