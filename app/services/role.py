from typing import List

from app.models.admin import Api, Menu, Role
from app.repositories.role import role_repository


class RoleService:
    def __init__(self):
        self.repo = role_repository

    async def get(self, id: int):
        return await self.repo.get(id=id)

    async def list(self, page: int, page_size: int, search=None, order=None):
        from tortoise.expressions import Q
        return await self.repo.list(page=page, page_size=page_size, search=search or Q(), order=order or [])

    async def create(self, obj_in):
        return await self.repo.create(obj_in=obj_in)

    async def update(self, id: int, obj_in):
        return await self.repo.update(id=id, obj_in=obj_in)

    async def remove(self, id: int):
        await self.repo.remove(id=id)

    async def is_exist(self, name: str) -> bool:
        return await self.repo.is_exist(name=name)

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


role_service = RoleService()
