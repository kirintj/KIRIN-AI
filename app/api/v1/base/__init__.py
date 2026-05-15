from fastapi import APIRouter

from .base import router
from .captcha import router as captcha_router

base_router = APIRouter()
base_router.include_router(router, tags=["基础模块TEST"])
base_router.include_router(captcha_router, tags=["验证码"])

__all__ = ["base_router"]
