from typing import List, Optional, Tuple

from tortoise.expressions import Q

from app.models.admin import AuditLog
from app.repositories.base import RepositoryBase, Total


class AuditLogRepository(RepositoryBase):
    def __init__(self):
        super().__init__(AuditLog)

    async def list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: Optional[list] = None,
    ) -> Tuple[Total, List]:
        return await super().list(page, page_size, search, order=order or ["-created_at"])


auditlog_repository = AuditLogRepository()
