from app.tools.base import BaseTool
from app.utils.chat import call_llm

OPTIMIZE_PROMPT = """你是一个专业的简历优化助手。请根据以下信息，对简历进行针对该 JD 的定向优化。

原始简历：
{resume_text}

目标 JD：
{jd_text}

匹配分析：
{match_result}

请输出以下内容：

## 修改建议
（逐条列出需要修改的地方，说明原因）

## 优化后简历
（输出完整的优化后简历文本，直接可用于投递）

注意：
1. 保持简历真实性，不要编造经历
2. 优化措辞，突出与 JD 相关的经验
3. 用数据和成果说话
4. 调整关键词以匹配 JD"""


class OptimizeTool(BaseTool):
    name = "optimize_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        resume_text = kwargs.get("resume_text", "")
        jd_text = kwargs.get("jd_text", "")
        match_result = kwargs.get("match_result", "")

        if not resume_text or not jd_text or not match_result:
            return "缺少必要参数：resume_text、jd_text、match_result"

        prompt = OPTIMIZE_PROMPT.format(
            resume_text=resume_text,
            jd_text=jd_text,
            match_result=match_result,
        )
        return await call_llm(prompt, max_tokens=4000, temperature=0.7)
