import logging

from fastapi import APIRouter
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success
from app.services.business import memory_service

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/memory")
async def get_user_memory(
    current_user: User = DependAuth,
):
    history = await memory_service.get_memory(current_user.username)
    data = [{"user": u, "assistant": a} for u, a in history]
    return Success(data=data)


@router.delete("/memory")
async def clear_user_memory(
    current_user: User = DependAuth,
):
    await memory_service.clear_memory(current_user.username)
    return Success(data={"message": "对话记忆已清空"})
