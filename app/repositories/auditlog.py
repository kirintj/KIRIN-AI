
from tortoise.expressions import Q

from app.models.admin import AuditLog


class AuditLogRepository:
    def __init__(self):
        self.model = AuditLog

    async def list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
    ):
        total = await self.model.filter(search).count()
        records = await self.model.filter(search).order_by("-created_at").offset((page - 1) * page_size).limit(page_size)
        return total, records


auditlog_repository = AuditLogRepository()
