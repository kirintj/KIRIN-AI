import json
from abc import ABC, abstractmethod
from typing import Any


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
        """将 RAG 检索结果格式化为上下文文本和来源列表。"""
        if not docs or (len(docs) == 1 and docs[0].get("source") == ""):
            return empty_msg, []
        context_parts = [f"[文档{i+1}] {d['content']}" for i, d in enumerate(docs) if d.get("content")]
        sources = list(set(d.get("source", "") for d in docs if d.get("source")))
        return "\n\n".join(context_parts), sources
