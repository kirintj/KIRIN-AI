import logging

from app.utils.chat import call_llm
from app.agent.rules import get_engine, reload_rules

_logger = logging.getLogger(__name__)

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


async def route_intent_rules(query: str) -> str | None:
    """基于规则引擎的意图路由，返回 None 表示无法确定"""
    engine = get_engine()
    result = engine.match(query)
    if result:
        _logger.debug("rule match: %s -> %s (rule: %s)", query[:50], result.intent, result.rule_name)
        return result.intent
    return None


async def route_intent_llm(query: str) -> str:
    """基于 LLM 的意图路由（兜底）"""
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
    """统一意图路由入口

    - use_llm=True: 强制使用 LLM 路由
    - use_llm=False: 规则引擎优先，匹配失败时 LLM 兜底
    """
    if use_llm:
        return await route_intent_llm(query)

    # 规则引擎优先
    result = await route_intent_rules(query)
    if result is not None:
        return result

    # LLM 兜底
    _logger.debug("rule miss, fallback to LLM: %s", query[:50])
    return await route_intent_llm(query)
