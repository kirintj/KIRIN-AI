from app.repositories.menu import menu_repository


class MenuService:
    def __init__(self):
        self.repo = menu_repository

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

    async def get_by_menu_path(self, path: str):
        return await self.repo.get_by_menu_path(path)

    async def get_menu_tree(self):
        all_menus = await self.repo.model.all().order_by("order")
        menu_dict_map = {}
        for menu in all_menus:
            menu_dict_map[menu.id] = await menu.to_dict()
            menu_dict_map[menu.id]["children"] = []

        for menu in all_menus:
            if menu.parent_id != 0 and menu.parent_id in menu_dict_map:
                menu_dict_map[menu.parent_id]["children"].append(menu_dict_map[menu.id])

        return [menu_dict_map[menu.id] for menu in all_menus if menu.parent_id == 0]

    async def count_children(self, parent_id: int) -> int:
        return await self.repo.model.filter(parent_id=parent_id).count()


menu_service = MenuService()
