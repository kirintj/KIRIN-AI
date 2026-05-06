from fastapi import APIRouter

from app.schemas.base import Success
from app.schemas.config import ConfigUpdate
from app.services.config import sysconfig_service

router = APIRouter()


@router.get("/ai", summary="获取AI模型配置")
async def get_ai_config():
    data = await sysconfig_service.get_ai_config()
    return Success(data=data)


@router.post("/ai", summary="更新AI模型配置")
async def update_ai_config(req_in: ConfigUpdate):
    data = await sysconfig_service.update_ai_config([c.model_dump() for c in req_in.configs])
    return Success(data=data, msg="配置更新成功")
