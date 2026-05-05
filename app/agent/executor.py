import json
from app.agent.router import route_intent
from app.tools.base import BaseTool
from app.tools.rag_tool import RAGTool
from app.tools.todo_tool import TodoTool
from app.tools.interview_tool import InterviewTool
from app.tools.salary_tool import SalaryTool
from app.tools.guide_tool import GuideTool
from app.tools.feedback_tool import FeedbackTool
from app.tools.tracker_tool import TrackerTool
from app.utils.chat import call_llm
from app.memory.memory import get_memory, save_memory, get_raw_history
from app.rag.pipeline import AdvancedRAGPipeline, PipelineConfig


class AgentExecutor:
    def __init__(self, use_llm_router: bool = False):
        self.tools: dict[str, BaseTool] = {}
        self.use_llm_router = use_llm_router
        self._recommend_pipeline = AdvancedRAGPipeline(PipelineConfig(
            enable_query_rewrite=True,
            enable_rerank=True,
            enable_context_compress=False,
            top_k=3,
        ))
        self._register_default_tools()

    def _register_default_tools(self):
        default_tools = [
            RAGTool(),
            TodoTool(),
            InterviewTool(),
            SalaryTool(),
            GuideTool(),
            FeedbackTool(),
            TrackerTool(),
        ]
        for tool in default_tools:
            self.tools[tool.name] = tool

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool

    async def run(self, query: str, user_id: str = "default") -> str:
        tool_name = await route_intent(query, use_llm=self.use_llm_router)

        if tool_name == "workflow":
            result = await self._run_workflow(query, user_id)
        elif tool_name == "chat":
            history = get_memory(user_id)
            prompt = self._build_chat_prompt(query, history)
            result = await call_llm(prompt)
        else:
            tool = self.tools.get(tool_name)
            if not tool:
                return f"未找到工具：{tool_name}"
            result = await tool.run(query, user_id=user_id)

        recommendation = await self._build_personalized_recommendation(user_id, query)
        if recommendation:
            result = f"{result}\n\n---\n\n{recommendation}"

        save_memory(user_id, query, result)
        return result

    async def _run_workflow(self, query: str, user_id: str) -> str:
        """多步骤工作流：先检索知识，再创建待办，最后汇总"""
        rag_tool = self.tools.get("rag_tool")
        todo_tool = self.tools.get("todo_tool")

        steps = []

        if rag_tool:
            rag_result = await rag_tool.run(query)
            steps.append(f"📋 知识检索结果：\n{rag_result}")
        else:
            rag_result = ""

        if todo_tool:
            todo_content = rag_result or query
            todo_result = await todo_tool.run(todo_content)
            steps.append(f"✅ 待办创建结果：\n{todo_result}")

        summary_prompt = f"用户请求：{query}\n\n执行结果：\n" + "\n\n".join(steps) + "\n\n请综合以上结果，给出简洁的汇总回复。"
        summary = await call_llm(summary_prompt)
        steps.append(f"📝 汇总：\n{summary}")

        return "\n\n---\n\n".join(steps)

    def _build_chat_prompt(self, query: str, history: list[tuple[str, str]]) -> str:
        parts = []
        for user_msg, ai_msg in history[-5:]:
            parts.append(f"用户：{user_msg}")
            parts.append(f"助手：{ai_msg}")
        parts.append(f"用户：{query}")
        parts.append("助手：")
        return "\n".join(parts)

    async def _build_personalized_recommendation(self, user_id: str, current_query: str) -> str:
        """基于用户历史提取偏好标签，再调用 RAG 检索个性化内容"""
        history = get_raw_history(user_id)
        if len(history) < 3:
            return ""

        history_text = "\n".join(
            f"用户：{item['user']}\n助手：{item['assistant'][:200]}"
            for item in history[-10:]
        )

        preferences = await self._extract_preferences(history_text)
        if not preferences:
            return ""

        search_query = self._build_search_query(preferences)
        if not search_query:
            return ""

        docs = await self._recommend_pipeline.search(search_query)
        if not docs or (len(docs) == 1 and docs[0].get("source") == ""):
            return ""

        rag_context = "\n\n".join(
            f"[资料{i+1}] {d['content'][:300]}" for i, d in enumerate(docs) if d.get("content")
        )

        prompt = (
            "你是一个个性化求职推荐助手。请根据用户的偏好标签和检索到的相关资料，生成简短的个性化推荐。\n\n"
            f"用户偏好：{json.dumps(preferences, ensure_ascii=False)}\n\n"
            f"检索到的相关资料：\n{rag_context}\n\n"
            "请生成 2-3 条简短的个性化推荐，每条包含推荐内容和推荐理由。\n"
            "格式：\n💡 **个性化推荐**\n1. [推荐内容] — [推荐理由]\n2. [推荐内容] — [推荐理由]\n\n"
            "注意：推荐要具体、贴合用户偏好，避免泛泛而谈。"
        )
        return await call_llm(prompt, max_tokens=800, temperature=0.7)

    async def _extract_preferences(self, history_text: str) -> dict | None:
        """从对话历史中提取用户偏好标签"""
        prompt = (
            "你是一个用户画像分析助手。请根据以下用户对话历史，提取用户的求职偏好标签。\n\n"
            f"对话历史：\n{history_text}\n\n"
            '请以 JSON 格式输出偏好标签：\n'
            '{"industry": "目标行业", "position": "目标岗位", "city": "目标城市", '
            '"skills": ["核心技能"], "experience_level": "经验等级", '
            '"concerns": ["关注问题"]}\n\n'
            '只输出 JSON。信息不足的字段输出空字符串或空数组。'
        )
        raw = await call_llm(prompt, max_tokens=500, temperature=0.1)
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            preferences = json.loads(cleaned.strip())
            has_value = any(
                preferences.get(k) for k in ("industry", "position", "city", "skills", "concerns")
            )
            return preferences if has_value else None
        except (json.JSONDecodeError, AttributeError):
            return None

    @staticmethod
    def _build_search_query(preferences: dict) -> str:
        """基于偏好标签构建 RAG 检索 query"""
        parts = []
        for key in ("industry", "position", "city"):
            val = preferences.get(key, "")
            if val:
                parts.append(val)
        skills = preferences.get("skills", [])
        if skills:
            parts.extend(skills[:3])
        concerns = preferences.get("concerns", [])
        if concerns:
            parts.extend(concerns[:2])
        if not parts:
            return ""
        return " ".join(parts)
