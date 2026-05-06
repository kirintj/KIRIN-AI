from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.core.ctx import CTX_USER_ID
from app.models import User
from app.settings import settings


class AuthControl:
    @classmethod
    async def is_authed(cls, token: str = Header(..., description="token验证")) -> Optional["User"]:
        try:
            decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
            token_type = decode_data.get("type", "access")
            if token_type != "access":
                raise HTTPException(status_code=401, detail="请使用Access Token访问")
            user_id = decode_data.get("user_id")
            if not user_id:
                raise HTTPException(status_code=401, detail="Token 中缺少用户信息")
            user = await User.filter(id=user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="用户不存在")
            if not user.is_active:
                raise HTTPException(status_code=401, detail="用户已被禁用")
            CTX_USER_ID.set(int(user_id))
            return user
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="无效的Token")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="登录已过期")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"认证异常: {repr(e)}")


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path
        roles = await current_user.roles.all().prefetch_related("apis")
        if not roles:
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        permission_apis: set[tuple[str, str]] = set()
        for role in roles:
            for api in role.apis:
                permission_apis.add((api.method, api.path))
        if (method, path) not in permission_apis:
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")


DependAuth = Depends(AuthControl.is_authed)
DependPermission = Depends(PermissionControl.has_permission)
