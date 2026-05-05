from app.models.admin import Role
from app.repositories.base import RepositoryBase
from app.schemas.roles import RoleCreate, RoleUpdate


class RoleRepository(RepositoryBase[Role, RoleCreate, RoleUpdate]):
    def __init__(self):
        super().__init__(model=Role)

    async def is_exist(self, name: str) -> bool:
        return await self.model.filter(name=name).exists()


role_repository = RoleRepository()
