from app.tools.base import BaseTool
from app.rag.pipeline import PipelineConfig, AdvancedRAGPipeline
from app.utils.chat import call_llm

SALARY_PROMPT = """你是一个专业的薪资谈判助手。请根据以下检索到的薪资报告和企业薪资结构文档，为用户生成数据支撑的薪资谈判建议。

城市：{city}
行业：{industry}
岗位：{position}
工作年限：{experience}
期望薪资：{expected_salary}

检索到的相关薪资文档：
{doc_context}

请生成以下内容：

## 薪资数据参考
（基于文档中的薪资报告，给出该城市/行业/岗位的薪资范围、中位数、分位数）

## 谈判话术建议
（基于数据的薪资谈判话术，包含开场、论证、回应压价等环节）

## 谈判切入点
（基于企业薪资结构文档，给出最佳谈判角度和策略）

## 注意事项
（薪资谈判中的常见陷阱和应对方法）

注意：
1. 所有薪资数据必须基于检索到的文档，如文档无数据则明确说明
2. 话术要专业且有说服力，避免过于激进
3. 结合用户期望薪资给出调整建议"""


class SalaryTool(BaseTool):
    name = "salary_tool"

    def __init__(self):
        self._pipeline = AdvancedRAGPipeline(PipelineConfig(
            enable_query_rewrite=False,
            enable_rerank=False,
            enable_context_compress=False,
            top_k=5,
        ))

    async def run(self, query: str = "", **kwargs) -> str:
        city = kwargs.get("city", "")
        industry = kwargs.get("industry", "")
        position = kwargs.get("position", "")
        experience = kwargs.get("experience", "")
        expected_salary = kwargs.get("expected_salary", "面议")

        search_query = f"{city} {industry} {position} 薪资报告 薪资结构"
        docs = await self._pipeline.search(search_query, collection_name="salary")

        doc_context, sources = self.build_rag_context(docs, "暂无该城市/行业/岗位的薪资文档，将基于通用经验生成建议。")

        prompt = SALARY_PROMPT.format(
            city=city,
            industry=industry,
            position=position,
            experience=experience,
            expected_salary=expected_salary,
            doc_context=doc_context,
        )
        answer = await call_llm(prompt, max_tokens=3000, temperature=0.7)

        if sources:
            answer += f"\n\n参考文档来源：{', '.join(sources)}"
        return answer

