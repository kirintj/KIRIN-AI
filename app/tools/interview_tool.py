from app.tools.base import BaseTool
from app.rag.chromadb_client import search_chromadb
from app.utils.chat import call_llm

INTERVIEW_PROMPT = """你是一个专业的面试准备助手。请根据以下检索到的面试题库和企业文化文档，为用户生成个性化的面试应答。

目标企业：{company}
目标岗位：{position}
面试类型：{interview_type}

检索到的相关文档：
{doc_context}

请生成以下内容：

## 面试题目预测（5-8道）
（基于企业过往面试题和岗位要求，预测可能被问到的问题）

## 个性化应答建议
（针对每道题目，结合用户岗位和企业文化，给出应答框架和要点）

## 考察逻辑解析
（解析高频问题背后的考察点，帮助用户理解面试官意图）

## 面试注意事项
（基于企业文化文档，给出该企业面试的特殊注意事项）

注意：
1. 应答要贴合企业风格和文化
2. 突出岗位匹配的核心能力
3. 提供应答框架而非固定话术，方便用户个性化调整"""


class InterviewTool(BaseTool):
    name = "interview_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        company = kwargs.get("company", "")
        position = kwargs.get("position", "")
        interview_type = kwargs.get("interview_type", "综合面试")

        search_query = f"{company} {position} 面试题 企业文化"
        docs = await search_chromadb(search_query, top_k=5, collection_name="interview")

        doc_context, sources = self._build_context(docs)

        prompt = INTERVIEW_PROMPT.format(
            company=company,
            position=position,
            interview_type=interview_type,
            doc_context=doc_context,
        )
        answer = await call_llm(prompt, max_tokens=4000, temperature=0.7)

        if sources:
            answer += f"\n\n参考文档来源：{', '.join(sources)}"
        return answer

    @staticmethod
    def _build_context(docs: list[dict]) -> tuple[str, list[str]]:
        if not docs or (len(docs) == 1 and docs[0].get("source") == ""):
            return "暂无该企业/岗位的面试文档，将基于通用面试经验生成建议。", []
        context_parts = [f"[文档{i+1}] {d['content']}" for i, d in enumerate(docs) if d.get("content")]
        sources = list(set(d.get("source", "") for d in docs if d.get("source")))
        return "\n\n".join(context_parts), sources
