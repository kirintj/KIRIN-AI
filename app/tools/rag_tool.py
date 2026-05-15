from app.tools.base import BaseTool
from app.rag.pipeline import AdvancedRAGPipeline, PipelineConfig


class RAGTool(BaseTool):
    name = "rag_tool"

    def __init__(self):
        self._pipeline = AdvancedRAGPipeline()

    async def run(self, query: str = "", **kwargs) -> str:
        result = await self._pipeline.search_and_generate(query)
        answer = result["answer"]
        sources = result.get("sources", [])
        source_info = f"\n\n参考文档来源：{', '.join(sources)}" if sources else ""
        return answer + source_info

    async def run_with_collection(self, query: str, collection_name: str, top_k: int = 5) -> dict:
        pipeline = AdvancedRAGPipeline()
        result = await pipeline.search_and_generate(query, collection_name=collection_name, top_k=top_k)
        return result
