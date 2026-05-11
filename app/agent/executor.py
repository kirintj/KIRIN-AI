from app.agent.router import route_intent
from app.agent.common import build_personalized_recommendation
from app.tools.base import BaseTool
from app.tools.registry import create_default_tools
from app.utils.chat import call_llm
from app.services.business import memory_service


class AgentExecutor:
    def __init__(self, use_llm_router: bool = False):
        self.tools: dict[str, BaseTool] = {}
        self.use_llm_router = use_llm_router
        self._register_default_tools()

    def _register_default_tools(self):
        self.tools = create_default_tools()

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool

    async def run(self, query: str, user_id: str, use_llm_router: bool | None = None) -> str:
        use_llm = use_llm_router if use_llm_router is not None else self.use_llm_router
        tool_name = await route_intent(query, use_llm=use_llm)

        if tool_name == "workflow":
            result = await self._run_workflow(query, user_id)
        elif tool_name == "chat":
            history = await memory_service.get_memory(user_id)
            prompt = self._build_chat_prompt(query, history)
            result = await call_llm(prompt)
        else:
            tool = self.tools.get(tool_name)
            if not tool:
                return f"未找到工具：{tool_name}"
            result = await tool.run(query, user_id=user_id)

        recommendation = await build_personalized_recommendation(user_id, query)
        if recommendation:
            result = f"{result}\n\n---\n\n{recommendation}"

        await memory_service.save_memory(user_id, query, result)
        return result

    async def _run_workflow(self, query: str, user_id: str) -> str:
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

    @staticmethod
    def _build_chat_prompt(query: str, history: list[tuple[str, str]]) -> str:
        parts = []
        for user_msg, ai_msg in history[-5:]:
            parts.append(f"用户：{user_msg}")
            parts.append(f"助手：{ai_msg}")
        parts.append(f"用户：{query}")
        parts.append("助手：")
        return "\n".join(parts)
