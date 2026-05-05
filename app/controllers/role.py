from typing import List

from app.core.crud import CRUDBase
from app.models.admin import Api, Menu, Role
from app.schemas.roles import RoleCreate, RoleUpdate


class RoleController(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def __init__(self):
        super().__init__(model=Role)

    async def is_exist(self, name: str) -> bool:
        return await self.model.filter(name=name).exists()

    async def update_roles(self, role: Role, menu_ids: List[int], api_infos: List[dict]) -> None:
        await role.menus.clear()
        if menu_ids:
            menu_objs = await Menu.filter(id__in=menu_ids)
            await role.menus.add(*menu_objs)

        await role.apis.clear()
        if api_infos:
            conditions = []
            for item in api_infos:
                conditions.append((item.get("path"), item.get("method")))
            api_objs = await Api.filter(
                path__in=[c[0] for c in conditions],
                method__in=[c[1] for c in conditions],
            )
            matched = [
                api_obj for api_obj in api_objs
                if (api_obj.path, api_obj.method) in set(conditions)
            ]
            await role.apis.add(*matched)


role_controller = RoleController()
