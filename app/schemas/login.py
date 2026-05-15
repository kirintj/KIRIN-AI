from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class CredentialsSchema(BaseModel):
    username: str = Field(..., description="用户名称", example="admin")
    password: str = Field(..., description="密码", example="123456")
    captcha_id: str = Field(..., description="验证码ID")
    x: int = Field(..., description="滑块x坐标")


class JWTPayload(BaseModel):
    user_id: int
    username: str
    is_superuser: bool
    exp: datetime
    type: Literal["access", "refresh"] = "access"


class JWTOut(BaseModel):
    access_token: str
    refresh_token: str
    username: str


class RefreshTokenIn(BaseModel):
    refresh_token: str = Field(..., description="刷新令牌")
