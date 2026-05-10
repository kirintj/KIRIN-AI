from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: int) -> ModelType:
        return await self.model.get(id=id)

    async def get_or_none(self, **kwargs) -> ModelType | None:
        return await self.model.filter(**kwargs).first()

    async def exists(self, **kwargs) -> bool:
        return await self.model.filter(**kwargs).exists()

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list | None = None) -> Tuple[Total, List[ModelType]]:
        order = order or []
        query = self.model.filter(search)
        total: int = await query.count()
        items: List[ModelType] = await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)
        return Total(total), items

    async def list_all(self, search: Q = Q(), order: list | None = None) -> List[ModelType]:
        order = order or []
        return await self.model.filter(search).order_by(*order)

    async def create(self, obj_in: CreateSchemaType | Dict) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = {k: v for k, v in obj_in.items() if k != "id"}
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})
        obj = await self.get(id=id)
        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def remove(self, id: int) -> None:
        obj = await self.get(id=id)
        await obj.delete()
