"""服务注册表：统一管理服务实例，支持未来服务发现。"""

import logging
from typing import Any, Callable

_logger = logging.getLogger(__name__)


class ServiceInfo:
    """服务元信息"""

    def __init__(
        self,
        name: str,
        instance: Any,
        version: str = "1.0.0",
        tags: list[str] | None = None,
    ):
        self.name = name
        self.instance = instance
        self.version = version
        self.tags = tags or []
        self.healthy = True


class ServiceRegistry:
    """服务注册表（单例）"""

    def __init__(self):
        self._services: dict[str, ServiceInfo] = {}

    def register(
        self,
        name: str,
        instance: Any,
        version: str = "1.0.0",
        tags: list[str] | None = None,
    ) -> None:
        """注册服务"""
        self._services[name] = ServiceInfo(
            name=name,
            instance=instance,
            version=version,
            tags=tags,
        )
        _logger.info("service registered: %s v%s", name, version)

    def get(self, name: str) -> Any | None:
        """获取服务实例"""
        info = self._services.get(name)
        if info and info.healthy:
            return info.instance
        return None

    def get_info(self, name: str) -> ServiceInfo | None:
        """获取服务元信息"""
        return self._services.get(name)

    def list_services(self) -> list[dict]:
        """列出所有服务"""
        return [
            {
                "name": info.name,
                "version": info.version,
                "tags": info.tags,
                "healthy": info.healthy,
            }
            for info in self._services.values()
        ]

    def set_healthy(self, name: str, healthy: bool) -> None:
        """设置服务健康状态"""
        if name in self._services:
            self._services[name].healthy = healthy


# 全局单例
_registry: ServiceRegistry | None = None


def get_registry() -> ServiceRegistry:
    """获取全局服务注册表"""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry
