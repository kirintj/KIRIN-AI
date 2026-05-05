from datetime import datetime

from tortoise.expressions import Q

from app.repositories.auditlog import auditlog_repository


class AuditLogService:
    def __init__(self):
        self.repo = auditlog_repository

    async def list(self, page: int, page_size: int, search: Q = Q()):
        return await self.repo.list(page=page, page_size=page_size, search=search)


auditlog_service = AuditLogService()
