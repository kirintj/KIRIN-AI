from app.tools.base import RAGToolBase

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


class SalaryTool(RAGToolBase):
    name = "salary_tool"
    COLLECTION_NAME = "salary"
    PROMPT_TEMPLATE = SALARY_PROMPT
    empty_msg = "暂无该城市/行业/岗位的薪资文档，将基于通用经验生成建议。"

    def build_search_query(self, query: str, **kwargs) -> str:
        city = kwargs.get("city", "")
        industry = kwargs.get("industry", "")
        position = kwargs.get("position", "")
        return f"{city} {industry} {position} 薪资报告 薪资结构"

    def build_prompt_vars(self, query: str, **kwargs) -> dict:
        return {
            "city": kwargs.get("city", ""),
            "industry": kwargs.get("industry", ""),
            "position": kwargs.get("position", ""),
            "experience": kwargs.get("experience", ""),
            "expected_salary": kwargs.get("expected_salary", "面议"),
        }
