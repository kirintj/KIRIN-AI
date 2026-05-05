from app.tools.base import BaseTool
from app.tools.rag_tool import RAGTool
from app.tools.todo_tool import TodoTool
from app.utils.chat import call_llm

INTENT_PROMPT = """你是一个意图识别助手。根据用户输入，判断应该使用哪个工具处理。

可选工具：
- rag_tool：知识问答、信息检索、文档查询
- todo_tool：待办任务创建、提醒、日程管理
- tracker_tool：求职进度追踪、投递记录、申请管理、面试进度
- interview_tool：面试问答、面试题生成、面试准备、企业面试
- salary_tool：薪资谈判、薪资查询、薪资报告、薪酬
- guide_tool：求职攻略、求职指南、跨行业求职、跳槽建议
- feedback_tool：反馈评分、意见提交、评价结果
- workflow：多步骤任务，如"总结文档并生成待办"、"分析并创建任务"
- chat：普通聊天、闲聊、通用问题

用户输入：{query}

请只回复工具名称（rag_tool / todo_tool / tracker_tool / interview_tool / salary_tool / guide_tool / feedback_tool / workflow / chat），不要回复其他内容。"""


def route_intent_simple(query: str) -> str:
    """基于关键词的简单意图路由"""
    workflow_keywords = ["总结", "并", "然后", "之后", "同时"]
    todo_keywords = ["待办", "提醒", "任务", "日程", "计划", "todo", "记住", "别忘了", "别忘", "记得", "安排", "预约"]
    todo_action_keywords = ["要去做", "需要做", "准备去", "要去", "得去", "得做", "要完成"]
    time_keywords = ["下午", "明天", "今晚", "周", "号要", "点去", "点做", "点开"]
    rag_keywords = ["查询", "搜索", "文档", "知识", "检索", "资料"]
    interview_keywords = ["面试", "面试题", "面试准备", "面试应答", "面试技巧", "hr面", "技术面"]
    salary_keywords = ["薪资", "薪水", "薪酬", "工资", "谈判", "薪资报告", "薪资范围"]
    guide_keywords = ["攻略", "指南", "跨行业", "跳槽", "求职策略", "求职建议", "转行"]
    feedback_keywords = ["反馈", "评分", "评价", "意见", "打分"]
    tracker_keywords = ["投递", "申请", "进度", "追踪", "已投", "面试结果", "录用", "offer", "拒了", "简历投", "投了", "求职记录", "申请记录"]

    has_todo = any(kw in query for kw in todo_keywords)
    has_todo_action = any(kw in query for kw in todo_action_keywords)
    has_time = any(kw in query for kw in time_keywords)
    has_rag = any(kw in query for kw in rag_keywords)
    has_workflow = any(kw in query for kw in workflow_keywords)
    has_interview = any(kw in query for kw in interview_keywords)
    has_salary = any(kw in query for kw in salary_keywords)
    has_guide = any(kw in query for kw in guide_keywords)
    has_feedback = any(kw in query for kw in feedback_keywords)
    has_tracker = any(kw in query for kw in tracker_keywords)

    is_todo_intent = has_todo or (has_todo_action and has_time) or (has_todo_action)

    if has_feedback:
        return "feedback_tool"
    if has_tracker:
        return "tracker_tool"
    if has_interview:
        return "interview_tool"
    if has_salary:
        return "salary_tool"
    if has_guide:
        return "guide_tool"
    if is_todo_intent and (has_rag or has_workflow):
        return "workflow"
    if is_todo_intent:
        return "todo_tool"
    if has_rag:
        return "rag_tool"
    return "chat"


async def route_intent_llm(query: str) -> str:
    """基于 LLM 的意图路由"""
    prompt = INTENT_PROMPT.format(query=query)
    result = await call_llm(prompt)
    result = result.strip().lower()

    valid_tools = [
        "rag_tool", "todo_tool", "tracker_tool", "interview_tool",
        "salary_tool", "guide_tool", "feedback_tool",
        "workflow", "chat",
    ]
    for tool in valid_tools:
        if tool in result:
            return tool
    return "chat"


async def route_intent(query: str, use_llm: bool = False) -> str:
    """统一意图路由入口"""
    if use_llm:
        return await route_intent_llm(query)
    return route_intent_simple(query)
