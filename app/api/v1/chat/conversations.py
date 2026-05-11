import logging

from fastapi import APIRouter
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.business import CreateConversationRequest, RenameConversationRequest
from app.services.business import conversation_service

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/conversations/recent")
async def get_recent(
    limit: int = 5,
    current_user: User = DependAuth,
):
    convs = await conversation_service.get_recent(current_user.username, limit)
    return Success(data=convs)


@router.get("/conversations")
async def get_conversations(
    current_user: User = DependAuth,
):
    convs = await conversation_service.list_conversations(current_user.username)
    return Success(data=convs)


@router.post("/conversations")
async def create_new_conversation(
    request: CreateConversationRequest,
    current_user: User = DependAuth,
):
    conv = await conversation_service.create_conversation(current_user.username, request.title or "新对话")
    return Success(data=conv)


@router.put("/conversations/rename")
async def rename_existing_conversation(
    request: RenameConversationRequest,
    current_user: User = DependAuth,
):
    result = await conversation_service.rename_conversation(request.conversation_id, current_user.username, request.title)
    if result:
        return Success(data={"message": "重命名成功"})
    return Fail(code=404, msg="会话不存在")


@router.delete("/conversations/delete")
async def delete_existing_conversation(
    conversation_id: int,
    current_user: User = DependAuth,
):
    success = await conversation_service.delete_conversation(conversation_id, current_user.username)
    if success:
        return Success(data={"message": "会话已删除"})
    return Fail(code=404, msg="会话不存在")


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = DependAuth,
):
    messages = await conversation_service.get_messages_if_owner(conversation_id, current_user.username)
    if messages is None:
        return Fail(code=404, msg="会话不存在")
    return Success(data=messages)
