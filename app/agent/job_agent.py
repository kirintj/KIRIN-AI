import asyncio
import json

from app.agent.executor import AgentExecutor
from app.tools.base import build_rag_context
from app.tools.resume_tool import ResumeTool
from app.tools.jd_tool import JDTool
from app.tools.match_tool import MatchTool
from app.tools.optimize_tool import OptimizeTool
from app.tools.plan_tool import PlanTool
from app.rag.pipeline import AdvancedRAGPipeline
from app.utils.chat import call_llm

RESUME_SUMMARY_PROMPT = """请将以下结构化简历数据，用 200 字以内概括核心信息（技能、经验亮点、教育背景）：

{resume_json}

只输出概括文本，不要其他内容。"""

RAG_RESUME_OPTIMIZE_PROMPT = """你是一个专业的简历优化助手。请结合以下检索到的同行业优秀简历和目标岗位JD文档，对简历进行定向优化。

原始简历：
{resume_text}

目标 JD：
{jd_text}

匹配分析：
{match_result}

检索到的相关文档（优秀简历范例+岗位要求）：
{rag_context}

请输出以下内容：

## 修改建议
（逐条列出需要修改的地方，说明原因，参考检索到的优秀简历范例）

## 优化后简历
（输出完整的优化后简历文本，直接可用于投递）

## 简历匹配度报告
（从关键词匹配、经历相关性、技能覆盖度等维度评估，给出匹配度评分和改进建议）

注意：
1. 保持简历真实性，不要编造经历
2. 参考优秀简历的表述方式优化措辞
3. 用数据和成果说话
4. 调整关键词以匹配 JD"""


class JobAgent(AgentExecutor):
    """求职助手，扩展 AgentExecutor，增加简历/JD/匹配等专用工具。"""

    def __init__(self):
        super().__init__()
        self.resume_tool = ResumeTool()
        self.jd_tool = JDTool()
        self.match_tool = MatchTool()
        self.optimize_tool = OptimizeTool()
        self.plan_tool = PlanTool()
        self._resume_pipeline = AdvancedRAGPipeline()

    async def analyze_resume(self, resume_text: str) -> dict:
        result = await self.resume_tool.run(resume_text=resume_text)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}

    async def analyze_jd(self, jd_text: str) -> dict:
        result = await self.jd_tool.run(jd_text=jd_text)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}

    async def calculate_match(self, resume_json: str, jd_json: str) -> dict:
        result = await self.match_tool.run(resume_json=resume_json, jd_json=jd_json)
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"raw": result}

    async def optimize_resume(self, resume_text: str, jd_text: str, match_result: str) -> str:
        return await self.optimize_tool.run(
            resume_text=resume_text, jd_text=jd_text, match_result=match_result
        )

    async def optimize_resume_with_rag(
        self, resume_text: str, jd_text: str, match_result: str, user_id: int = 0
    ) -> dict:
        search_query = f"{jd_text} 优秀简历 岗位要求"
        docs = await self._resume_pipeline.search(search_query, collection_name="resume", user_id=user_id)

        rag_context, sources = build_rag_context(docs)

        prompt = RAG_RESUME_OPTIMIZE_PROMPT.format(
            resume_text=resume_text,
            jd_text=jd_text,
            match_result=match_result,
            rag_context=rag_context,
        )
        answer = await call_llm(prompt, max_tokens=5000, temperature=0.7)

        return {
            "optimized_resume": answer,
            "sources": sources,
        }

    async def generate_plan(self, resume_summary: str, jd_text: str, match_result: str) -> str:
        return await self.plan_tool.run(
            resume_summary=resume_summary, jd_text=jd_text, match_result=match_result
        )

    async def create_todos_from_plan(self, plan_text: str) -> str:
        todo_tool = self.tools.get("todo_tool")
        if not todo_tool:
            return "未找到待办工具"

        extract_prompt = f"""请从以下投递计划中，提取出所有可执行的任务项，每行一个任务，格式为：
- [ ] 任务描述

投递计划：
{plan_text}

只输出任务列表，不要其他内容。"""
        tasks_text = await call_llm(extract_prompt, max_tokens=1500, temperature=0.3)
        tasks = [
            line.replace("- [ ]", "").strip()
            for line in tasks_text.split("\n")
            if line.strip().startswith("- [ ]")
        ]

        created = []
        for task in tasks:
            if task:
                result = await todo_tool.run(task)
                created.append(result)

        if created:
            return f"已创建 {len(created)} 个待办任务：\n" + "\n".join(
                f"  {i + 1}. {t}" for i, t in enumerate(tasks[:len(created)])
            )
        return "未能提取到可执行任务"

    async def _get_resume_summary(self, resume_json: str) -> str:
        prompt = RESUME_SUMMARY_PROMPT.format(resume_json=resume_json)
        return await call_llm(prompt, max_tokens=500, temperature=0.3)

    async def generate_interview(
        self, company: str, position: str, interview_type: str = "综合面试"
    ) -> str:
        tool = self.tools.get("interview_tool")
        if not tool:
            return "未找到面试工具"
        return await tool.run(
            company=company, position=position, interview_type=interview_type
        )

    async def generate_salary_advice(
        self,
        city: str,
        industry: str,
        position: str,
        experience: str = "",
        expected_salary: str = "面议",
    ) -> str:
        tool = self.tools.get("salary_tool")
        if not tool:
            return "未找到薪资工具"
        return await tool.run(
            city=city, industry=industry, position=position,
            experience=experience, expected_salary=expected_salary,
        )

    async def generate_guide(self, scenario: str, goal: str = "成功求职") -> str:
        tool = self.tools.get("guide_tool")
        if not tool:
            return "未找到攻略工具"
        return await tool.run(scenario=scenario, goal=goal)

    async def full_pipeline(self, resume_text: str, jd_text: str) -> dict:
        steps = {}

        parsed_resume, parsed_jd = await asyncio.gather(
            self.analyze_resume(resume_text),
            self.analyze_jd(jd_text),
        )
        steps["resume"] = parsed_resume
        steps["jd"] = parsed_jd

        resume_json = json.dumps(parsed_resume, ensure_ascii=False)
        jd_json = json.dumps(parsed_jd, ensure_ascii=False)

        match_result, resume_summary = await asyncio.gather(
            self.calculate_match(resume_json, jd_json),
            self._get_resume_summary(resume_json),
        )
        steps["match"] = match_result

        match_str = json.dumps(match_result, ensure_ascii=False)
        optimized, plan = await asyncio.gather(
            self.optimize_resume_with_rag(resume_text, jd_text, match_str),
            self.generate_plan(resume_summary, jd_text, match_str),
        )
        steps["optimized_resume"] = optimized
        steps["plan"] = plan

        todo_result = await self.create_todos_from_plan(plan)
        steps["todos"] = todo_result

        return steps
