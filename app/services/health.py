"""健康检查：服务、数据库、外部依赖。"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

_logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CheckResult:
    name: str
    status: HealthStatus
    message: str = ""
    latency_ms: float = 0


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self._checks: dict[str, Any] = {}

    def register_check(self, name: str, check_fn: Any) -> None:
        """注册健康检查函数"""
        self._checks[name] = check_fn

    async def check_all(self) -> dict:
        """执行所有健康检查"""
        results: list[CheckResult] = []
        overall = HealthStatus.HEALTHY

        for name, check_fn in self._checks.items():
            try:
                t0 = time.monotonic()
                if asyncio.iscoroutinefunction(check_fn):
                    ok, msg = await check_fn()
                else:
                    ok, msg = check_fn()
                latency = (time.monotonic() - t0) * 1000

                status = HealthStatus.HEALTHY if ok else HealthStatus.UNHEALTHY
                results.append(CheckResult(name=name, status=status, message=msg, latency_ms=round(latency, 2)))

                if not ok:
                    overall = HealthStatus.UNHEALTHY

            except Exception as e:
                results.append(CheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e)[:200],
                ))
                overall = HealthStatus.UNHEALTHY

        return {
            "status": overall.value,
            "checks": [
                {
                    "name": r.name,
                    "status": r.status.value,
                    "message": r.message,
                    "latency_ms": r.latency_ms,
                }
                for r in results
            ],
        }


# 全局实例
_checker: HealthChecker | None = None


def get_health_checker() -> HealthChecker:
    """获取全局健康检查器"""
    global _checker
    if _checker is None:
        _checker = HealthChecker()
    return _checker
