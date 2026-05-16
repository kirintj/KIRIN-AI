from fastapi import APIRouter
from datetime import datetime, timezone
import logging

from app.settings import settings
from app.utils.chat import _get_client, convert_messages_for_api, get_ai_config
from app.schemas.chat import ChatResponse, ChatRequest, ChatMessage
from app.schemas.base import Success, Fail
from app.core.dependency import DependAuth
from app.services.chat import chat_service
from app.models.admin import User

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.post("/chat")
async def chat(
        request: ChatRequest,
        current_user: User = DependAuth,
):
    try:
        username = current_user.username

        await chat_service.create_record(
            username=username,
            role="user",
            content=request.messages[-1].content,
            timestamp=datetime.now(timezone.utc),
        )

        config = await get_ai_config()
        default_model = config.get("model_name", settings.MODEL_NAME)
        client = _get_client(config.get("api_key") or settings.API_KEY or "", config.get("base_url") or settings.BASE_URL or "")

        api_message = convert_messages_for_api(request.messages)
        response = await client.chat.completions.create(
            model=request.model or default_model,
            messages=api_message,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=False,
        )

        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content or ""
            assistant_message = ChatMessage(
                role="assistant",
                content=content,
                timestamp=datetime.now().isoformat(),
            )

            await chat_service.create_record(
                username=username,
                role="assistant",
                content=content,
                timestamp=datetime.now(timezone.utc),
            )

            chat_response = ChatResponse(
                message=assistant_message,
                model=response.model,
                usage=response.usage.model_dump() if response.usage else None,
            )
            return Success(data=chat_response.model_dump())

        return Fail(code=500, msg="AI模型返回了空响应")

    except Exception:
        _logger.exception("处理聊天请求时发生错误")
        return Fail(code=500, msg="处理聊天请求时发生错误，请稍后重试")


@router.get("/models")
async def get_models(
        current_user: User = DependAuth,
):
    try:
        config = await get_ai_config()
        default_model = config.get("model_name", settings.MODEL_NAME)
        client = _get_client(config.get("api_key") or settings.API_KEY or "", config.get("base_url") or settings.BASE_URL or "")
        models = await client.models.list()
        data = {
            "models": [model.id for model in models.data],
            "default_model": default_model,
            "user": current_user.username,
        }
        return Success(data=data)
    except Exception:
        config = await get_ai_config()
        default_model = config.get("model_name", settings.MODEL_NAME)
        data = {
            "models": [default_model],
            "default_model": default_model,
            "user": current_user.username,
        }
        return Success(data=data)


@router.get("/history")
async def get_user_history(
    current_user: User = DependAuth,
):
    records = await chat_service.get_history_by_username(current_user.username)
    data = [
        {
            "role": record.role,
            "content": record.content,
            "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        }
        for record in records
    ]
    return Success(data=data)


@router.delete("/history")
async def clear_user_history(
    current_user: User = DependAuth,
):
    count = await chat_service.clear_history_by_username(current_user.username)
    data = {
        "message": "历史已清空",
        "user": current_user.username,
        "deleted": count,
        "time": datetime.now(timezone.utc).isoformat(),
    }
    return Success(data=data)


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0",
        "database": "tortoise-orm",
    }
