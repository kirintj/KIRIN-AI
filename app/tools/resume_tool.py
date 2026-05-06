from app.tools.base import BaseTool
from app.utils.chat import call_llm

RESUME_PARSE_PROMPT = """你是一个专业的简历解析助手。请将以下简历文本解析为结构化 JSON 数据。

要求提取以下字段：
- name: 姓名
- phone: 电话
- email: 邮箱
- skills: 技能列表（数组）
- education: 教育背景（数组，每项含 school/major/degree/year）
- experience: 工作/项目经历（数组，每项含 company_or_project/role/duration/description）
- summary: 个人优势总结

简历文本：
{resume_text}

请严格输出 JSON 格式，不要输出其他内容。如果某个字段无法提取，设为 null 或空数组。"""


class ResumeTool(BaseTool):
    name = "resume_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        resume_text = kwargs.get("resume_text", query)
        prompt = RESUME_PARSE_PROMPT.format(resume_text=resume_text)
        result = await call_llm(prompt, max_tokens=3000, temperature=0.3)
        return self.clean_json(result)
