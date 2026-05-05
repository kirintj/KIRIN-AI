import json
from app.tools.base import BaseTool
from app.utils.chat import call_llm

JD_PARSE_PROMPT = """你是一个专业的岗位描述（JD）分析助手。请将以下 JD 文本解析为结构化 JSON 数据。

要求提取以下字段：
- title: 岗位名称
- company: 公司名称（如有）
- required_skills: 必备技能列表（数组）
- preferred_skills: 加分技能列表（数组）
- responsibilities: 岗位职责（数组）
- experience_years: 经验要求（如 "3-5年"）
- education: 学历要求
- keywords: 核心关键词（用于匹配，数组）
- direction: 岗位方向（如 后端/前端/AI/全栈/数据 等）

JD 文本：
{jd_text}

请严格输出 JSON 格式，不要输出其他内容。如果某个字段无法提取，设为 null 或空数组。"""


class JDTool(BaseTool):
    name = "jd_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        jd_text = kwargs.get("jd_text", query)
        prompt = JD_PARSE_PROMPT.format(jd_text=jd_text)
        result = await call_llm(prompt, max_tokens=2000, temperature=0.3)
        return self.clean_json(result)
