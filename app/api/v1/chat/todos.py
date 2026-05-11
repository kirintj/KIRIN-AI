import logging
from typing import Optional

from fastapi import APIRouter
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.business import TodoIdRequest, TodoUpdateRequest, TodoCreateRequest
from app.services.business import todo_service

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/todos")
async def list_todos(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    done: Optional[bool] = None,
    current_user: User = DependAuth,
):
    todos = await todo_service.list_todos(current_user.username)
    if category:
        todos = [t for t in todos if t.get("category") == category]
    if priority:
        todos = [t for t in todos if t.get("priority") == priority]
    if done is not None:
        todos = [t for t in todos if t.get("done") == done]
    return Success(data=todos)


@router.post("/todos")
async def create_todo(
    request: TodoCreateRequest,
    current_user: User = DependAuth,
):
    todo_item = await todo_service.create_todo(
        user_id=current_user.username,
        content=request.content,
        priority=request.priority,
        category=request.category,
        due_date=request.due_date,
    )
    return Success(data=todo_item)


@router.put("/todos/toggle")
async def toggle_todo(
    request: TodoIdRequest,
    current_user: User = DependAuth,
):
    result = await todo_service.toggle_todo(request.id, current_user.username)
    if result:
        return Success(data={"message": "状态已切换"})
    return Fail(code=400, msg="待办不存在")


@router.put("/todos")
async def update_todo(
    request: TodoUpdateRequest,
    current_user: User = DependAuth,
):
    updates = {k: v for k, v in request.model_dump().items() if k != "id" and v is not None}
    result = await todo_service.update_todo(request.id, current_user.username, **updates)
    if result:
        return Success(data={"message": "待办已更新"})
    return Fail(code=400, msg="待办不存在")


@router.delete("/todos")
async def delete_todo(
    id: int,
    current_user: User = DependAuth,
):
    success = await todo_service.delete_todo(id, current_user.username)
    if success:
        return Success(data={"message": "待办已删除"})
    return Fail(code=400, msg="待办不存在")


@router.delete("/todos/completed")
async def clear_completed_todos(
    current_user: User = DependAuth,
):
    removed = await todo_service.clear_completed(current_user.username)
    return Success(data={"message": f"已清除 {removed} 条已完成待办", "removed": removed})
