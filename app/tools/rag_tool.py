from app.tools.base import BaseTool
from app.rag.pipeline import AdvancedRAGPipeline, PipelineConfig


class RAGTool(BaseTool):
    name = "rag_tool"

    def __init__(self):
        self._pipeline = AdvancedRAGPipeline()

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = int(kwargs.get("user_id", 0))
        result = await self._pipeline.search_and_generate(query, user_id=user_id)
        answer = result["answer"]
        sources = result.get("sources", [])
        source_info = f"\n\n参考文档来源：{', '.join(sources)}" if sources else ""
        return answer + source_info

    async def run_with_collection(self, query: str, collection_name: str, top_k: int = 5, user_id: int = 0) -> dict:
        pipeline = AdvancedRAGPipeline()
        result = await pipeline.search_and_generate(query, collection_name=collection_name, top_k=top_k, user_id=user_id)
        return result
