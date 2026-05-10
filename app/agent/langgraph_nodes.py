import json
from app.agent.langgraph_state import JobAssistantState
from app.agent.router import route_intent
from app.agent.common import (
    build_personalized_recommendation,
    extract_preferences,
    build_search_query,
    parse_json_response,
)
from app.tools.rag_tool import RAGTool
from app.tools.todo_tool import TodoTool
from app.tools.interview_tool import InterviewTool
from app.tools.salary_tool import SalaryTool
from app.tools.guide_tool import GuideTool
from app.tools.feedback_tool import FeedbackTool
from app.utils.chat import call_llm
from app.memory.memory import save_memory, get_memory

_rag_tool = RAGTool()
_todo_tool = TodoTool()
_interview_tool = InterviewTool()
_salary_tool = SalaryTool()
_guide_tool = GuideTool()
_feedback_tool = FeedbackTool()

TOOL_MAP = {
    "rag_tool": _rag_tool,
    "todo_tool": _todo_tool,
    "interview_tool": _interview_tool,
    "salary_tool": _salary_tool,
    "guide_tool": _guide_tool,
    "feedback_tool": _feedback_tool,
}

INTENT_CLASSIFY_PROMPT = """你是一个意图识别与参数提取助手。根据用户输入，判断意图并提取参数。

可选意图：
- rag_tool：知识问答、信息检索、文档查询
- todo_tool：待办任务创建、提醒、日程管理
- interview_tool：面试问答、面试题生成、面试准备
- salary_tool：薪资谈判、薪资查询、薪酬报告
- guide_tool：求职攻略、求职指南、跨行业求职、跳槽建议
- feedback_tool：反馈评分、意见提交
- workflow：需要多步骤协作（如"查资料并创建待办"）
- chat：普通聊天、闲聊

用户输入：{query}

请以 JSON 格式回复：
{{"intent": "意图名", "tool_args": {{"key": "value"}}, "need_more": false}}

need_more 为 true 表示执行完当前工具后还需要继续调用其他工具。
只输出 JSON，不要其他内容。"""


async def intent_router_node(state: JobAssistantState) -> dict:
    query = state.get("query", "")
    use_llm = state.get("use_llm_router", False)

    if use_llm:
        prompt = INTENT_CLASSIFY_PROMPT.format(query=query)
        raw = await call_llm(prompt, max_tokens=500, temperature=0.1)
        parsed = parse_json_response(raw)
        if parsed:
            intent = parsed.get("intent", "chat")
            tool_args = parsed.get("tool_args", {})
            need_more = parsed.get("need_more", False)
        else:
            intent = await route_intent(query, use_llm=True)
            tool_args = {}
            need_more = False
    else:
        intent = await route_intent(query, use_llm=False)
        tool_args = _extract_simple_args(intent, query)
        need_more = intent == "workflow"

    return {
        "intent": intent,
        "tool_name": intent if intent in TOOL_MAP else "",
        "tool_args": tool_args,
        "need_more": need_more,
        "iteration": state.get("iteration", 0),
    }


def _extract_simple_args(intent: str, query: str) -> dict:
    if intent == "interview_tool":
        parts = query.replace("面试", "").strip().split()
        return {"company": parts[0] if len(parts) > 0 else "", "position": parts[1] if len(parts) > 1 else ""}
    if intent == "salary_tool":
        return {"city": "", "industry": "", "position": query}
    if intent == "guide_tool":
        return {"scenario": query}
    return {}


async def tool_executor_node(state: JobAssistantState) -> dict:
    tool_name = state.get("tool_name", "")
    query = state.get("query", "")
    tool_args = state.get("tool_args", {})
    user_id = state.get("user_id", "default")

    if not tool_name or tool_name not in TOOL_MAP:
        answer = await _chat_fallback(query, state)
        return {"tool_output": answer, "final_answer": answer, "iteration": state.get("iteration", 0) + 1}

    tool = TOOL_MAP[tool_name]
    tool_args["user_id"] = user_id
    result = await tool.run(query=query, **tool_args)

    iteration = state.get("iteration", 0) + 1
    return {"tool_output": result, "iteration": iteration}


async def should_continue(state: JobAssistantState) -> str:
    if state.get("need_more") and state.get("iteration", 0) < state.get("max_iterations", 3):
        if state.get("intent") == "workflow":
            return "workflow_continue"
        return "tool_selector"
    return "response_builder"


async def workflow_continue_node(state: JobAssistantState) -> dict:
    query = state.get("query", "")
    tool_output = state.get("tool_output", "")
    iteration = state.get("iteration", 0)
    user_id = state.get("user_id", "default")

    if iteration == 1:
        todo_result = await _todo_tool.run(tool_output or query, user_id=user_id)
        combined = f"📋 知识检索结果：\n{tool_output}\n\n✅ 待办创建结果：\n{todo_result}"
        return {"tool_output": combined, "need_more": False, "iteration": iteration + 1}

    return {"need_more": False, "iteration": iteration + 1}


async def response_builder_node(state: JobAssistantState) -> dict:
    tool_output = state.get("tool_output", "")
    query = state.get("query", "")
    user_id = state.get("user_id", "default")

    if tool_output:
        final_answer = tool_output
    else:
        final_answer = await _chat_fallback(query, state)

    recommendation = await build_personalized_recommendation(user_id, query)
    if recommendation:
        final_answer = f"{final_answer}\n\n---\n\n{recommendation}"

    await save_memory(user_id, query, final_answer)
    return {"final_answer": final_answer}


async def _chat_fallback(query: str, state: JobAssistantState) -> str:
    history = await get_memory(state.get("user_id", "default"))
    parts = []
    for user_msg, ai_msg in history[-5:]:
        parts.append(f"用户：{user_msg}")
        parts.append(f"助手：{ai_msg}")
    parts.append(f"用户：{query}")
    parts.append("助手：")
    return await call_llm("\n".join(parts))
