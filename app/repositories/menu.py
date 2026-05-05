from typing import Optional

from app.models.admin import Menu
from app.repositories.base import RepositoryBase
from app.schemas.menus import MenuCreate, MenuUpdate


class MenuRepository(RepositoryBase[Menu, MenuCreate, MenuUpdate]):
    def __init__(self):
        super().__init__(model=Menu)

    async def get_by_menu_path(self, path: str) -> Optional[Menu]:
        return await self.model.filter(path=path).first()


menu_repository = MenuRepository()
