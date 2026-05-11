from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr = Field(example="admin@qq.com")
    username: str = Field(example="admin")
    password: str = Field(example="123456", min_length=6, max_length=128)
    avatar: Optional[str] = Field(default=None, description="用户头像URL/文件存储路径")
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = Field(None, description="部门ID")

    def create_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"role_ids"})


class UserRegister(BaseModel):
    """Registration schema — no privilege escalation fields."""
    email: EmailStr = Field(example="admin@qq.com")
    username: str = Field(example="admin")
    password: str = Field(example="123456", min_length=6, max_length=128)
    avatar: Optional[str] = Field(default=None, description="用户头像URL/文件存储路径")

    def create_dict(self):
        return self.model_dump(exclude_unset=True)


class UserUpdate(BaseModel):
    id: int
    email: EmailStr
    username: str
    avatar: Optional[str] = None
    is_active: Optional[bool] = True
    password: Optional[str] = None
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = None


class UpdatePassword(BaseModel):
    old_password: str = Field(description="旧密码")
    new_password: str = Field(description="新密码", min_length=6, max_length=128)
