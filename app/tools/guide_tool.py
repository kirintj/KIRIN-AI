from app.tools.base import BaseTool
from app.rag.pipeline import PipelineConfig, AdvancedRAGPipeline
from app.utils.chat import call_llm

GUIDE_PROMPT = """你是一个专业的求职攻略助手。请根据以下检索到的求职攻略文档，为用户生成步骤化的行动指南。

用户场景：{scenario}
目标：{goal}

检索到的相关攻略文档：
{doc_context}

请生成以下内容：

## 场景分析
（分析用户当前求职场景的特点和挑战）

## 步骤化行动指南
（按阶段给出具体可执行的步骤，每步包含：目标、具体行动、预期成果）

## 关键资源推荐
（关联攻略中提到的工具、模板、网站等资源）

## 常见误区提醒
（该场景下求职者常犯的错误及规避方法）

## 时间规划建议
（给出合理的时间安排建议）

注意：
1. 所有建议必须基于检索到的文档内容，确保专业性和准确性
2. 步骤要具体可执行，避免泛泛而谈
3. 结合用户场景给出个性化建议"""


class GuideTool(BaseTool):
    name = "guide_tool"

    def __init__(self):
        self._pipeline = AdvancedRAGPipeline(PipelineConfig(
            enable_query_rewrite=False,
            enable_rerank=False,
            enable_context_compress=False,
            top_k=5,
        ))

    async def run(self, query: str = "", **kwargs) -> str:
        scenario = kwargs.get("scenario", query)
        goal = kwargs.get("goal", "成功求职")

        search_query = f"{scenario} 求职攻略"
        docs = await self._pipeline.search(search_query, collection_name="map-draw")

        doc_context, sources = self.build_rag_context(docs, "暂无该场景的攻略文档，将基于通用求职经验生成建议。")

        prompt = GUIDE_PROMPT.format(
            scenario=scenario,
            goal=goal,
            doc_context=doc_context,
        )
        answer = await call_llm(prompt, max_tokens=3000, temperature=0.7)

        if sources:
            answer += f"\n\n参考文档来源：{', '.join(sources)}"
        return answer

