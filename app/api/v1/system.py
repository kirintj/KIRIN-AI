"""系统监控API：健康检查、指标暴露、任务队列。"""

import time

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success
from app.services.health import get_health_checker
from app.services.metrics import get_metrics
from app.services.registry import get_registry
from app.services.task_queue import get_task_queue, TaskStatus

router = APIRouter()


@router.get("/health", summary="健康检查")
async def health_check():
    checker = get_health_checker()
    result = await checker.check_all()
    status_code = 200 if result["status"] == "healthy" else 503
    return result


@router.get("/metrics", summary="Prometheus指标", response_class=PlainTextResponse)
async def metrics():
    collector = get_metrics()
    return collector.to_prometheus()


@router.get("/services", summary="服务注册表")
async def list_services(current_user: User = DependAuth):
    registry = get_registry()
    return Success(data={"services": registry.list_services()})


@router.get("/tasks", summary="任务队列状态")
async def list_tasks(status: str = "", current_user: User = DependAuth):
    queue = get_task_queue()
    task_status = TaskStatus(status) if status and status in TaskStatus.__members__.values() else None
    tasks = queue.list_tasks(task_status)
    return Success(data={
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "status": t.status.value,
                "created_at": t.created_at,
                "started_at": t.started_at,
                "completed_at": t.completed_at,
                "error": t.error,
            }
            for t in tasks[:50]
        ],
        "total": len(tasks),
    })
