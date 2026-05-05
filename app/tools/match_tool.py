import json
from app.tools.base import BaseTool
from app.utils.chat import call_llm

MATCH_PROMPT = """你是一个专业的简历-岗位匹配分析助手。请根据以下结构化简历和 JD 数据，进行匹配度分析。

简历数据：
{resume_json}

JD 数据：
{jd_json}

请输出以下 JSON 格式的分析结果：
{{
  "score": 匹配度评分（0-100的整数）,
  "matched_skills": ["已满足的技能1", "已满足的技能2"],
  "missing_skills": ["缺失的技能1", "缺失的技能2"],
  "strengths": ["优势1", "优势2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["改进建议1", "改进建议2"],
  "detail": "一段200字左右的综合分析说明"
}}

请严格输出 JSON 格式，不要输出其他内容。"""


class MatchTool(BaseTool):
    name = "match_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        resume_json = kwargs.get("resume_json", "")
        jd_json = kwargs.get("jd_json", "")

        if not resume_json or not jd_json:
            return json.dumps({"error": "缺少必要参数：resume_json 和 jd_json"})

        prompt = MATCH_PROMPT.format(resume_json=resume_json, jd_json=jd_json)
        result = await call_llm(prompt, max_tokens=2000, temperature=0.3)
        return self.clean_json(result)
