import logging
from typing import Optional

from fastapi import APIRouter

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.business import (
    CreateApplicationRequest, UpdateApplicationRequest, MoveApplicationRequest,
)
from app.services.business import tracker_service, STATUS_LIST, STATUS_LABELS, STATUS_COLORS

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/applications")
async def get_applications(
    status: Optional[str] = None,
    current_user: User = DependAuth,
):
    try:
        apps = await tracker_service.list_applications(current_user.username, status=status)
        return Success(data=apps)
    except Exception as e:
        _logger.warning("Tracker: list_applications failed: %s", e)
        return Success(data=[])


@router.post("/applications")
async def create_app(
    request: CreateApplicationRequest,
    current_user: User = DependAuth,
):
    if request.status and request.status not in STATUS_LIST:
        return Fail(code=400, msg=f"无效状态，可选值：{', '.join(STATUS_LIST)}")
    try:
        app = await tracker_service.create_application(current_user.username, **request.model_dump())
        return Success(data=app)
    except Exception as e:
        _logger.error("Tracker: create_application failed: %s", e)
        return Fail(code=500, msg="创建失败，请稍后重试")


@router.get("/applications/stats")
async def get_stats(
    current_user: User = DependAuth,
):
    try:
        stats = await tracker_service.get_stats(current_user.username)
        return Success(data=stats)
    except Exception as e:
        _logger.warning("Tracker: get_stats failed: %s", e)
        return Success(data={
            "total": 0,
            "by_status": {s: 0 for s in STATUS_LIST},
            "status_labels": STATUS_LABELS,
            "status_colors": STATUS_COLORS,
        })


@router.get("/applications/{app_id}")
async def get_app(
    app_id: int,
    current_user: User = DependAuth,
):
    try:
        app = await tracker_service.get_application(app_id, current_user.username)
        if not app:
            return Fail(code=404, msg="记录不存在")
        return Success(data=app)
    except Exception as e:
        _logger.warning("Tracker: get_application failed: %s", e)
        return Fail(code=500, msg="查询失败")


@router.put("/applications")
async def update_app(
    request: UpdateApplicationRequest,
    current_user: User = DependAuth,
):
    try:
        updates = {k: v for k, v in request.model_dump().items() if k != "app_id" and v is not None}
        result = await tracker_service.update_application(request.app_id, current_user.username, **updates)
        if result:
            return Success(data={"message": "更新成功"})
        return Fail(code=404, msg="记录不存在")
    except Exception as e:
        _logger.error("Tracker: update_application failed: %s", e)
        return Fail(code=500, msg="更新失败")


@router.put("/applications/move")
async def move_app(
    request: MoveApplicationRequest,
    current_user: User = DependAuth,
):
    try:
        result = await tracker_service.move_application(request.app_id, current_user.username, request.status)
        if result:
            return Success(data={"message": "状态已更新"})
        return Fail(code=400, msg="操作失败，请检查状态值是否有效")
    except Exception as e:
        _logger.error("Tracker: move_application failed: %s", e)
        return Fail(code=500, msg="操作失败")


@router.delete("/applications")
async def delete_app(
    app_id: int,
    current_user: User = DependAuth,
):
    try:
        success = await tracker_service.delete_application(app_id, current_user.username)
        if success:
            return Success(data={"message": "记录已删除"})
        return Fail(code=404, msg="记录不存在")
    except Exception as e:
        _logger.error("Tracker: delete_application failed: %s", e)
        return Fail(code=500, msg="删除失败")
