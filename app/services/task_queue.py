"""异步任务队列：内存实现，支持未来切换到Redis/Celery。"""

import asyncio
import logging
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

_logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0
    completed_at: float = 0
    metadata: dict = field(default_factory=dict)


class TaskQueue:
    """内存任务队列"""

    def __init__(self, max_concurrent: int = 5):
        self._queue: deque[Task] = deque()
        self._tasks: dict[str, Task] = {}
        self._handlers: dict[str, Callable] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running = False

    def register_handler(self, task_name: str, handler: Callable) -> None:
        """注册任务处理器"""
        self._handlers[task_name] = handler

    async def submit(self, task_name: str, metadata: dict | None = None) -> str:
        """提交任务，返回任务ID"""
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            name=task_name,
            metadata=metadata or {},
        )
        self._queue.append(task)
        self._tasks[task_id] = task

        _logger.info("task submitted: %s (%s)", task_id, task_name)
        asyncio.create_task(self._process(task))
        return task_id

    async def _process(self, task: Task) -> None:
        """处理单个任务"""
        handler = self._handlers.get(task.name)
        if not handler:
            task.status = TaskStatus.FAILED
            task.error = f"no handler for task: {task.name}"
            return

        async with self._semaphore:
            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            try:
                if asyncio.iscoroutinefunction(handler):
                    task.result = await handler(**task.metadata)
                else:
                    task.result = handler(**task.metadata)
                task.status = TaskStatus.COMPLETED
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)[:500]
                _logger.exception("task failed: %s", task.id)

            task.completed_at = time.time()
            elapsed = task.completed_at - task.started_at
            _logger.info("task done: %s (%s), status=%s, elapsed=%.2fs",
                        task.id, task.name, task.status.value, elapsed)

    def get_task(self, task_id: str) -> Task | None:
        """获取任务状态"""
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None) -> list[Task]:
        """列出任务"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)

    def cleanup(self, max_age: float = 3600) -> int:
        """清理已完成的旧任务"""
        now = time.time()
        to_remove = [
            task_id for task_id, task in self._tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            and now - task.completed_at > max_age
        ]
        for task_id in to_remove:
            del self._tasks[task_id]
        return len(to_remove)


# 全局单例
_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    """获取全局任务队列"""
    global _queue
    if _queue is None:
        _queue = TaskQueue()
    return _queue
