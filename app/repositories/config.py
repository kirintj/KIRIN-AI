from app.models.admin import SysConfig
from app.repositories.base import RepositoryBase


class SysConfigRepository(RepositoryBase[SysConfig, dict, dict]):
    def __init__(self):
        super().__init__(model=SysConfig)

    async def get_by_key(self, key: str) -> SysConfig | None:
        return await self.model.filter(key=key).first()

    async def upsert(self, key: str, value: str, desc: str | None = None) -> SysConfig:
        obj = await self.get_by_key(key)
        if obj:
            obj.value = value
            if desc is not None:
                obj.desc = desc
            await obj.save()
            return obj
        return await self.model.create(key=key, value=value, desc=desc)

    async def get_all_as_dict(self) -> dict[str, str]:
        configs = await self.model.all()
        return {c.key: c.value for c in configs}


sysconfig_repository = SysConfigRepository()
