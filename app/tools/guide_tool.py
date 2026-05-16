from app.tools.base import RAGToolBase

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


class GuideTool(RAGToolBase):
    name = "guide_tool"
    COLLECTION_NAME = "map-draw"
    PROMPT_TEMPLATE = GUIDE_PROMPT
    empty_msg = "暂无该场景的攻略文档，将基于通用求职经验生成建议。"

    def build_search_query(self, query: str, **kwargs) -> str:
        scenario = kwargs.get("scenario", query)
        return f"{scenario} 求职攻略"

    def build_prompt_vars(self, query: str, **kwargs) -> dict:
        return {
            "scenario": kwargs.get("scenario", query),
            "goal": kwargs.get("goal", "成功求职"),
        }
