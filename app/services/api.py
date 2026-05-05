from fastapi.routing import APIRoute

from app.log import logger
from app.models.admin import Api
from app.repositories.api import api_repository


class ApiService:
    def __init__(self):
        self.repo = api_repository

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

    async def refresh_api(self):
        from app import app

        all_api_list = []
        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                all_api_list.append((list(route.methods)[0], route.path_format))

        delete_api = []
        for api in await Api.all():
            if (api.method, api.path) not in all_api_list:
                delete_api.append((api.method, api.path))
        for item in delete_api:
            method, path = item
            logger.debug(f"API Deleted {method} {path}")
            await Api.filter(method=method, path=path).delete()

        for route in app.routes:
            if isinstance(route, APIRoute) and len(route.dependencies) > 0:
                method = list(route.methods)[0]
                path = route.path_format
                summary = route.summary
                tags = list(route.tags)[0]
                api_obj = await Api.filter(method=method, path=path).first()
                if api_obj:
                    await api_obj.update_from_dict(dict(method=method, path=path, summary=summary, tags=tags)).save()
                else:
                    logger.debug(f"API Created {method} {path}")
                    await Api.create(method=method, path=path, summary=summary, tags=tags)


api_service = ApiService()
