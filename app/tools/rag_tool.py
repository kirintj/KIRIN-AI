from app.tools.base import BaseTool
from app.rag.chromadb_client import search_chromadb, search_all_collections
from app.utils.chat import call_llm


class RAGTool(BaseTool):
    name = "rag_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        docs = await search_all_collections(query)
        if not docs:
            return "未检索到相关文档，请先添加知识库文档。"

        context_parts = []
        sources = []
        for idx, doc in enumerate(docs, 1):
            context_parts.append(f"[文档{idx}] {doc['content']}")
            if doc.get("source"):
                sources.append(doc["source"])

        context = "\n\n".join(context_parts)
        source_info = f"\n\n参考文档来源：{', '.join(set(sources))}" if sources else ""

        prompt = (
            f"基于以下检索到的文档内容回答问题。要求内容贴合文档、个性化强、逻辑清晰。"
            f"如果内容中没有相关信息，请说明无法回答。\n\n"
            f"参考资料：\n{context}\n\n问题：{query}"
        )
        answer = await call_llm(prompt)
        return answer + source_info

    async def run_with_collection(self, query: str, collection_name: str, top_k: int = 5) -> dict:
        docs = await search_chromadb(query, top_k=top_k, collection_name=collection_name)
        if not docs:
            return {"answer": "未检索到相关文档。", "sources": [], "documents": []}

        context_parts = []
        sources = []
        for idx, doc in enumerate(docs, 1):
            context_parts.append(f"[文档{idx}] {doc['content']}")
            if doc.get("source"):
                sources.append(doc["source"])

        context = "\n\n".join(context_parts)
        prompt = (
            f"基于以下检索到的文档内容回答问题，要求内容贴合文档、个性化强、逻辑清晰：\n\n"
            f"参考资料：\n{context}\n\n问题：{query}"
        )
        answer = await call_llm(prompt)

        return {
            "answer": answer,
            "sources": list(set(sources)),
            "documents": docs,
        }
