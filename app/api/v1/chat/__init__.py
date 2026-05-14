from fastapi import APIRouter

from app.core.dependency import DependPermission

from .chat import router
from .agent_chat import router as agent_router
from .todos import router as todos_router
from .feedback import router as feedback_router
from .memory import router as memory_router
from .conversations import router as conversations_router
from .chat_history import router as history_router
from .upload import router as upload_router
from .job_assistant import router as job_assistant_router
from .tracker import router as tracker_router
from .interview_sim import router as interview_sim_router
from .resume_export import router as resume_export_router
from .dashboard import router as dashboard_router

chat_router = APIRouter()
chat_router.include_router(router, tags=["chat模块"])
chat_router.include_router(agent_router, tags=["agent模块"])
chat_router.include_router(todos_router, tags=["待办模块"])
chat_router.include_router(feedback_router, tags=["反馈模块"])
chat_router.include_router(memory_router, tags=["记忆模块"])
chat_router.include_router(conversations_router, tags=["会话模块"])
chat_router.include_router(history_router, prefix="/history", tags=["对话历史模块"], dependencies=[DependPermission])
chat_router.include_router(upload_router, prefix="/upload", tags=["文件上传模块"])
chat_router.include_router(job_assistant_router, prefix="/job", tags=["求职助手模块"])
chat_router.include_router(tracker_router, prefix="/tracker", tags=["求职进度追踪模块"])
chat_router.include_router(interview_sim_router, prefix="/interview-sim", tags=["面试模拟模块"])
chat_router.include_router(resume_export_router, prefix="/resume-export", tags=["简历导出模块"])
chat_router.include_router(dashboard_router, prefix="/dashboard", tags=["数据仪表盘模块"])

__all__ = ["chat_router"]
