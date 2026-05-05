from datetime import datetime
from typing import List

from fastapi.exceptions import HTTPException

from app.repositories.user import user_repository
from app.repositories.role import role_repository
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


class UserService:
    def __init__(self):
        self.repo = user_repository

    async def get(self, id: int):
        return await self.repo.get(id=id)

    async def get_by_email(self, email: str):
        return await self.repo.get_by_email(email)

    async def get_by_username(self, username: str):
        return await self.repo.get_by_username(username)

    async def list(self, page: int, page_size: int, search=None, order=None):
        from tortoise.expressions import Q
        return await self.repo.list(page=page, page_size=page_size, search=search or Q(), order=order or [])

    async def create_user(self, obj_in: UserCreate):
        user_data = obj_in.create_dict()
        user_data['password'] = get_password_hash(password=obj_in.password)
        obj = await self.repo.create(user_data)
        return obj

    async def update(self, id: int, obj_in: UserUpdate):
        return await self.repo.update(id=id, obj_in=obj_in)

    async def remove(self, id: int):
        await self.repo.remove(id=id)

    async def update_last_login(self, id: int) -> None:
        user = await self.repo.get(id=id)
        user.last_login = datetime.now()
        await user.save()

    async def authenticate(self, credentials: CredentialsSchema):
        user = await self.repo.get_by_username(credentials.username)
        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return user

    async def update_roles(self, user, role_ids: List[int]) -> None:
        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await role_repository.get(id=role_id)
            await user.roles.add(role_obj)

    async def reset_password(self, user_id: int):
        user_obj = await self.repo.get(id=user_id)
        if user_obj.is_superuser:
            raise HTTPException(status_code=403, detail="不允许重置超级管理员密码")
        user_obj.password = get_password_hash(password="123456")
        await user_obj.save()


user_service = UserService()
