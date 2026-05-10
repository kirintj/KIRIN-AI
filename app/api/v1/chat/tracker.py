import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.services.business import tracker_service, STATUS_LIST

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
    app_id: int
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    contact: Optional[str] = None


class MoveApplicationRequest(BaseModel):
    app_id: int
    status: str


class AppIdRequest(BaseModel):
    app_id: int


@router.get("/applications")
async def get_applications(
    status: Optional[str] = None,
    current_user: User = DependAuth,
):
    apps = await tracker_service.list_applications(current_user.username, status=status)
    return Success(data=apps)


@router.post("/applications")
async def create_app(
    request: CreateApplicationRequest,
    current_user: User = DependAuth,
):
    if request.status and request.status not in STATUS_LIST:
        return Fail(code=400, msg=f"无效状态，可选值：{', '.join(STATUS_LIST)}")
    app = await tracker_service.create_application(current_user.username, **request.model_dump())
    return Success(data=app)


@router.get("/applications/stats")
async def get_stats(
    current_user: User = DependAuth,
):
    stats = await tracker_service.get_stats(current_user.username)
    return Success(data=stats)


@router.get("/applications/{app_id}")
async def get_app(
    app_id: int,
    current_user: User = DependAuth,
):
    app = await tracker_service.get_application(app_id, current_user.username)
    if not app:
        return Fail(code=404, msg="记录不存在")
    return Success(data=app)


@router.put("/applications")
async def update_app(
    request: UpdateApplicationRequest,
    current_user: User = DependAuth,
):
    updates = {k: v for k, v in request.model_dump().items() if k != "app_id" and v is not None}
    result = await tracker_service.update_application(request.app_id, current_user.username, **updates)
    if result:
        return Success(data={"message": "更新成功"})
    return Fail(code=404, msg="记录不存在")


@router.put("/applications/move")
async def move_app(
    request: MoveApplicationRequest,
    current_user: User = DependAuth,
):
    result = await tracker_service.move_application(request.app_id, current_user.username, request.status)
    if result:
        return Success(data={"message": "状态已更新"})
    return Fail(code=400, msg="操作失败，请检查状态值是否有效")


@router.delete("/applications")
async def delete_app(
    app_id: int,
    current_user: User = DependAuth,
):
    success = await tracker_service.delete_application(app_id, current_user.username)
    if success:
        return Success(data={"message": "记录已删除"})
    return Fail(code=404, msg="记录不存在")
