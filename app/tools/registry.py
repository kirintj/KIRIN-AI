"""共享工具注册表，避免 executor 和 job_agent 重复实例化工具。"""

from app.tools.base import BaseTool
from app.tools.rag_tool import RAGTool
from app.tools.todo_tool import TodoTool
from app.tools.interview_tool import InterviewTool
from app.tools.salary_tool import SalaryTool
from app.tools.guide_tool import GuideTool
from app.tools.feedback_tool import FeedbackTool
from app.tools.tracker_tool import TrackerTool


def create_default_tools() -> dict[str, BaseTool]:
    """创建默认工具集，返回 name→tool 映射。"""
    tools = [
        RAGTool(), TodoTool(), InterviewTool(),
        SalaryTool(), GuideTool(), FeedbackTool(), TrackerTool(),
    ]
    return {tool.name: tool for tool in tools}


# 模块级单例，供 agent 节点直接使用
TOOL_MAP: dict[str, BaseTool] = create_default_tools()
