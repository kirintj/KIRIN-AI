import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.tools.tracker_tool import (
    create_application, list_applications, get_application,
    update_application, delete_application, move_application,
    get_tracker_stats, STATUS_LIST,
)

router = APIRouter()
_logger = logging.getLogger(__name__)


class CreateApplicationRequest(BaseModel):
    company: str
    position: str
    status: Optional[str] = "applied"
    salary: Optional[str] = ""
    location: Optional[str] = ""
    source: Optional[str] = ""
    notes: Optional[str] = ""
    contact: Optional[str] = ""


class UpdateApplicationRequest(BaseModel):
    app_id: str
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    contact: Optional[str] = None


class MoveApplicationRequest(BaseModel):
    app_id: str
    status: str


class AppIdRequest(BaseModel):
    app_id: str


@router.get("/applications")
async def get_applications(
    status: Optional[str] = None,
    current_user: User = DependAuth,
):
    apps = list_applications(current_user.username, status=status)
    return Success(data=apps)


@router.post("/applications")
async def create_app(
    request: CreateApplicationRequest,
    current_user: User = DependAuth,
):
    if request.status and request.status not in STATUS_LIST:
        return Fail(code=400, msg=f"无效状态，可选值：{', '.join(STATUS_LIST)}")
    app = create_application(current_user.username, request.model_dump())
    return Success(data=app)


@router.get("/applications/stats")
async def get_stats(
    current_user: User = DependAuth,
):
    stats = get_tracker_stats(current_user.username)
    return Success(data=stats)


@router.get("/applications/{app_id}")
async def get_app(
    app_id: str,
    current_user: User = DependAuth,
):
    app = get_application(current_user.username, app_id)
    if not app:
        return Fail(code=404, msg="记录不存在")
    return Success(data=app)


@router.put("/applications")
async def update_app(
    request: UpdateApplicationRequest,
    current_user: User = DependAuth,
):
    updates = {k: v for k, v in request.model_dump().items() if k != "app_id" and v is not None}
    success = update_application(current_user.username, request.app_id, updates)
    if success:
        return Success(data={"message": "更新成功"})
    return Fail(code=404, msg="记录不存在")


@router.put("/applications/move")
async def move_app(
    request: MoveApplicationRequest,
    current_user: User = DependAuth,
):
    if request.status not in STATUS_LIST:
        return Fail(code=400, msg=f"无效状态，可选值：{', '.join(STATUS_LIST)}")
    success = move_application(current_user.username, request.app_id, request.status)
    if success:
        return Success(data={"message": "状态已更新"})
    return Fail(code=404, msg="记录不存在")


@router.delete("/applications")
async def delete_app(
    app_id: str,
    current_user: User = DependAuth,
):
    success = delete_application(current_user.username, app_id)
    if success:
        return Success(data={"message": "记录已删除"})
    return Fail(code=404, msg="记录不存在")
