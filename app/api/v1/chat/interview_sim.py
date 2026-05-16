import logging

from fastapi import APIRouter

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.business import CreateSessionRequest, InterviewChatRequest, SessionIdRequest
from app.tools.interview_sim_tool import (
    create_session, get_session, list_sessions,
    add_message_to_session, finish_session, delete_session,
    generate_interview_reply, evaluate_session,
    INTERVIEW_TYPES,
)

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/sessions")
async def get_sessions(current_user: User = DependAuth):
    sessions = await list_sessions(current_user.username)
    return Success(data=sessions)


@router.post("/sessions")
async def create_new_session(
    request: CreateSessionRequest,
    current_user: User = DependAuth,
):
    if request.interview_type and request.interview_type not in INTERVIEW_TYPES:
        return Fail(code=400, msg=f"无效面试类型，可选值：{', '.join(INTERVIEW_TYPES.keys())}")
    session = await create_session(current_user.username, request.model_dump())

    opening = f"你好！我是你的{INTERVIEW_TYPES.get(session['interview_type'], '技术')}面试官。"
    if request.company:
        opening += f"今天我们将模拟{request.company}的面试。"
    if request.position:
        opening += f"应聘岗位是{request.position}。"
    opening += "准备好了吗？我们先从第一个问题开始——请简单介绍一下你自己。"

    await add_message_to_session(current_user.username, session["id"], "assistant", opening)
    session["messages"] = [{"role": "assistant", "content": opening}]
    return Success(data=session)


@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: str,
    current_user: User = DependAuth,
):
    session = await get_session(current_user.username, session_id)
    if not session:
        return Fail(code=404, msg="面试会话不存在")
    return Success(data=session)


@router.post("/sessions/chat")
async def chat_in_session(
    request: InterviewChatRequest,
    current_user: User = DependAuth,
):
    session = await get_session(current_user.username, request.session_id)
    if not session:
        return Fail(code=404, msg="面试会话不存在")
    if session.get("status") == "completed":
        return Fail(code=400, msg="面试已结束")

    await add_message_to_session(current_user.username, request.session_id, "user", request.message)

    reply = await generate_interview_reply(session, request.message)

    await add_message_to_session(current_user.username, request.session_id, "assistant", reply)

    return Success(data={"reply": reply})


@router.post("/sessions/evaluate")
async def evaluate_interview(
    request: SessionIdRequest,
    current_user: User = DependAuth,
):
    session = await get_session(current_user.username, request.session_id)
    if not session:
        return Fail(code=404, msg="面试会话不存在")

    evaluation = await evaluate_session(session)
    await finish_session(current_user.username, request.session_id, evaluation)
    return Success(data=evaluation)


@router.delete("/sessions")
async def delete_interview_session(
    session_id: str,
    current_user: User = DependAuth,
):
    success = await delete_session(current_user.username, session_id)
    if success:
        return Success(data={"message": "面试会话已删除"})
    return Fail(code=404, msg="面试会话不存在")
