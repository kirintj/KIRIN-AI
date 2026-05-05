import json
from app.agent.langgraph_state import JobAssistantState
from app.agent.router import route_intent
from app.tools.rag_tool import RAGTool
from app.tools.todo_tool import TodoTool
from app.tools.interview_tool import InterviewTool
from app.tools.salary_tool import SalaryTool
from app.tools.guide_tool import GuideTool
from app.tools.feedback_tool import FeedbackTool
from app.utils.chat import call_llm
from app.memory.memory import save_memory, get_raw_history
from app.rag.chromadb_client import search_all_collections

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

PREFERENCE_EXTRACT_PROMPT = """你是一个用户画像分析助手。请根据以下用户对话历史，提取用户的求职偏好标签。

对话历史：
{history}

请以 JSON 格式输出偏好标签：
{{
  "industry": "目标行业（如 互联网/金融/教育，为空则输出 ""）",
  "position": "目标岗位（如 前端开发/产品经理，为空则输出 ""）",
  "city": "目标城市（如 北京/上海，为空则输出 ""）",
  "skills": ["用户提到的核心技能"],
  "experience_level": "经验等级（如 应届/1-3年/3-5年/5年以上，为空则输出 ""）",
  "concerns": ["用户关注的核心问题（如 薪资/面试/转行/简历优化）"]
}}

只输出 JSON，不要其他内容。如果历史信息不足以提取某个字段，该字段输出空字符串或空数组。"""

PERSONALIZED_RECOMMEND_PROMPT = """你是一个个性化求职推荐助手。请根据用户的偏好标签和检索到的相关资料，生成简短的个性化推荐。

用户偏好：
{preferences}

检索到的相关资料：
{rag_context}

请生成 2-3 条简短的个性化推荐，每条包含：
- 推荐内容（1-2 句话）
- 推荐理由（基于用户偏好）

格式要求：
💡 **个性化推荐**
1. [推荐内容] — [推荐理由]
2. [推荐内容] — [推荐理由]

注意：推荐要具体、贴合用户偏好，避免泛泛而谈。"""


async def intent_router_node(state: JobAssistantState) -> dict:
    query = state.get("query", "")
    use_llm = state.get("use_llm_router", False)

    if use_llm:
        prompt = INTENT_CLASSIFY_PROMPT.format(query=query)
        raw = await call_llm(prompt, max_tokens=500, temperature=0.1)
        try:
            parsed = json.loads(raw.strip().strip("`").strip())
            intent = parsed.get("intent", "chat")
            tool_args = parsed.get("tool_args", {})
            need_more = parsed.get("need_more", False)
        except (json.JSONDecodeError, AttributeError):
            intent = await route_intent(query, use_llm=True)
            tool_args = {}
            need_more = False
    else:
        intent = route_intent(query, use_llm=False)
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

    recommendation = await _build_personalized_recommendation(user_id, query)
    if recommendation:
        final_answer = f"{final_answer}\n\n---\n\n{recommendation}"

    save_memory(user_id, query, final_answer)
    return {"final_answer": final_answer}


async def _build_personalized_recommendation(user_id: str, current_query: str) -> str:
    """基于用户历史提取偏好标签，再调用 RAG 检索个性化内容"""
    history = get_raw_history(user_id)
    if len(history) < 3:
        return ""

    history_text = "\n".join(
        f"用户：{item['user']}\n助手：{item['assistant'][:200]}"
        for item in history[-10:]
    )

    preferences = await _extract_preferences(history_text)
    if not preferences:
        return ""

    search_query = _build_search_query(preferences, current_query)
    if not search_query:
        return ""

    docs = await search_all_collections(search_query, top_k=3)
    if not docs or (len(docs) == 1 and docs[0].get("source") == ""):
        return ""

    rag_context = "\n\n".join(
        f"[资料{i+1}] {d['content'][:300]}" for i, d in enumerate(docs) if d.get("content")
    )

    prompt = PERSONALIZED_RECOMMEND_PROMPT.format(
        preferences=json.dumps(preferences, ensure_ascii=False),
        rag_context=rag_context,
    )
    return await call_llm(prompt, max_tokens=800, temperature=0.7)


async def _extract_preferences(history_text: str) -> dict | None:
    """从对话历史中提取用户偏好标签"""
    prompt = PREFERENCE_EXTRACT_PROMPT.format(history=history_text)
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


def _build_search_query(preferences: dict, current_query: str) -> str:
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


async def _chat_fallback(query: str, state: JobAssistantState) -> str:
    from app.memory.memory import get_memory
    history = get_memory(state.get("user_id", "default"))
    parts = []
    for user_msg, ai_msg in history[-5:]:
        parts.append(f"用户：{user_msg}")
        parts.append(f"助手：{ai_msg}")
    parts.append(f"用户：{query}")
    parts.append("助手：")
    return await call_llm("\n".join(parts))
