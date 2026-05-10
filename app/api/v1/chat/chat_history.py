from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.core.dependency import DependAuth
from app.services.chat import chat_service
from app.models.chat import ChatHistory
from app.models.admin import User
from app.schemas.base import Success, SuccessExtra
from pydantic import BaseModel

router = APIRouter()


@router.get("/list", summary="获取对话历史列表（管理员）")
async def get_chat_history_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str = Query("", description="用户名称"),
    role: str = Query("", description="角色"),
    current_user: User = DependAuth,
):
    q = Q()
    if username:
        q &= Q(username__contains=username)
    if role:
        q &= Q(role=role)

    total = await ChatHistory.filter(q).count()
    records = await ChatHistory.filter(q).order_by("-timestamp").offset((page - 1) * page_size).limit(page_size)
    data = []
    for record in records:
        item = {
            "id": record.id,
            "username": record.username,
            "role": record.role,
            "content": record.content,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        }
        data.append(item)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/create", summary="创建对话记录")
async def create_chat_history(
    current_user: User = DependAuth,
    username: str = Query(..., description="用户名称"),
    role: str = Query(..., description="角色"),
    content: str = Query(..., description="消息内容"),
):
    record = await chat_service.create_record(
        username=username,
        role=role,
        content=content,
        timestamp=datetime.now(),
    )
    return Success(data={"id": record.id})


class ChatHistoryUpdate(BaseModel):
    id: int
    username: Optional[str] = None
    role: Optional[str] = None
    content: Optional[str] = None
    timestamp: Optional[str] = None


@router.post("/update", summary="更新对话记录")
async def update_chat_history(
    req_in: ChatHistoryUpdate,
    current_user: User = DependAuth,
):
    record = await ChatHistory.get(id=req_in.id)
    if req_in.username is not None:
        record.username = req_in.username
    if req_in.role is not None:
        record.role = req_in.role
    if req_in.content is not None:
        record.content = req_in.content
    if req_in.timestamp is not None:
        record.timestamp = datetime.fromisoformat(req_in.timestamp)
    await record.save()
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除对话记录")
async def delete_chat_history(
    id: int = Query(..., description="记录ID"),
    current_user: User = DependAuth,
):
    await ChatHistory.filter(id=id).delete()
    return Success(msg="删除成功")
