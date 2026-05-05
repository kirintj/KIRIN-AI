from tortoise.expressions import Q

from app.models.admin import Dept, DeptClosure
from app.repositories.base import RepositoryBase
from app.schemas.depts import DeptCreate, DeptUpdate


class DeptRepository(RepositoryBase[Dept, DeptCreate, DeptUpdate]):
    def __init__(self):
        super().__init__(model=Dept)

    async def get_dept_tree(self, name: str | None = None):
        q = Q(is_deleted=False)
        if name:
            q &= Q(name__contains=name)
        all_depts = await self.model.filter(q).order_by("order")

        def build_tree(parent_id):
            return [
                {
                    "id": dept.id,
                    "name": dept.name,
                    "desc": dept.desc,
                    "order": dept.order,
                    "parent_id": dept.parent_id,
                    "children": build_tree(dept.id),
                }
                for dept in all_depts
                if dept.parent_id == parent_id
            ]

        return build_tree(0)

    async def update_dept_closure(self, obj: Dept):
        parent_depts = await DeptClosure.filter(descendant=obj.parent_id)
        dept_closure_objs: list[DeptClosure] = []
        for item in parent_depts:
            dept_closure_objs.append(DeptClosure(ancestor=item.ancestor, descendant=obj.id, level=item.level + 1))
        dept_closure_objs.append(DeptClosure(ancestor=obj.id, descendant=obj.id, level=0))
        await DeptClosure.bulk_create(dept_closure_objs)

    async def delete_dept_closure(self, dept_id: int):
        await DeptClosure.filter(ancestor=dept_id).delete()
        await DeptClosure.filter(descendant=dept_id).delete()


dept_repository = DeptRepository()
