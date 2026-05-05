from app.tools.base import BaseTool
from app.utils.chat import call_llm

PLAN_PROMPT = """你是一个专业的求职规划助手。请根据以下信息，生成一份可执行的投递计划。

简历概要：
{resume_summary}

目标岗位 JD：
{jd_text}

匹配度分析：
{match_result}

请生成一份详细的投递计划，包含：

## 投递前准备（Day 1-2）
（具体任务，如修改简历某部分、准备面试题等）

## 投递执行（Day 3-5）
（具体行动，如投递哪些类型的公司、每天投递数量等）

## 面试准备（Day 5-7）
（针对该岗位的面试题准备、模拟面试等）

## 跟进与复盘
（投递后的跟进策略）

每项任务要具体可执行，格式为：
- [ ] 任务描述

请确保计划切实可行，时间安排合理。"""


class PlanTool(BaseTool):
    name = "plan_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        resume_summary = kwargs.get("resume_summary", "")
        jd_text = kwargs.get("jd_text", "")
        match_result = kwargs.get("match_result", "")

        if not resume_summary or not jd_text or not match_result:
            return "缺少必要参数：resume_summary、jd_text、match_result"

        prompt = PLAN_PROMPT.format(
            resume_summary=resume_summary,
            jd_text=jd_text,
            match_result=match_result,
        )
        return await call_llm(prompt, max_tokens=3000, temperature=0.7)
