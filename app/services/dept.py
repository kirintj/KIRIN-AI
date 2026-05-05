from tortoise.transactions import atomic

from app.repositories.dept import dept_repository


class DeptService:
    def __init__(self):
        self.repo = dept_repository

    async def get(self, id: int):
        return await self.repo.get(id=id)

    async def get_dept_tree(self, name: str | None = None):
        return await self.repo.get_dept_tree(name)

    @atomic()
    async def create_dept(self, obj_in):
        if obj_in.parent_id != 0:
            await self.repo.get(id=obj_in.parent_id)
        new_obj = await self.repo.create(obj_in=obj_in)
        await self.repo.update_dept_closure(new_obj)

    @atomic()
    async def update_dept(self, obj_in):
        dept_obj = await self.repo.get(id=obj_in.id)
        if dept_obj.parent_id != obj_in.parent_id:
            await self.repo.delete_dept_closure(dept_obj.id)
            await self.repo.update_dept_closure(dept_obj)
        dept_obj.update_from_dict(obj_in.model_dump(exclude_unset=True))
        await dept_obj.save()

    @atomic()
    async def delete_dept(self, dept_id: int):
        obj = await self.repo.get(id=dept_id)
        obj.is_deleted = True
        await obj.save()
        await self.repo.delete_dept_closure(dept_id)


dept_service = DeptService()
