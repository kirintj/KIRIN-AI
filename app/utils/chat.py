from typing import List, Dict
import httpx
from openai import AsyncOpenAI
import logging

from app.schemas.chat import ChatMessage, ChatRequest
from app.settings import settings
from app.core.constants import LLM_TIMEOUT_SECONDS, LLM_CONNECT_TIMEOUT_SECONDS

_logger = logging.getLogger(__name__)

LLM_TIMEOUT = LLM_TIMEOUT_SECONDS

# 缓存 client，配置变更时重建
_cached_client: AsyncOpenAI | None = None
_cached_api_key: str = ""
_cached_base_url: str = ""


def _get_client(api_key: str, base_url: str) -> AsyncOpenAI:
    global _cached_client, _cached_api_key, _cached_base_url
    if _cached_client is None or api_key != _cached_api_key or base_url != _cached_base_url:
        _cached_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(LLM_TIMEOUT, connect=LLM_CONNECT_TIMEOUT_SECONDS),
        )
        _cached_api_key = api_key
        _cached_base_url = base_url
    return _cached_client


async def get_ai_config() -> dict:
    from app.services.config import sysconfig_service
    return await sysconfig_service.get_ai_config()


def convert_messages_for_api(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


_DEFAULT_MAX_TOKENS = -1
_DEFAULT_TEMPERATURE = -1.0


async def call_llm(
    prompt: str,
    model: str | None = None,
    max_tokens: int = _DEFAULT_MAX_TOKENS,
    temperature: float = _DEFAULT_TEMPERATURE,
    timeout: float | None = None,
) -> str:
    config = await get_ai_config()
    effective_model = model or config.get("model_name", settings.MODEL_NAME)
    effective_max_tokens = max_tokens if max_tokens != _DEFAULT_MAX_TOKENS else int(config.get("max_tokens", 2000))
    effective_temperature = temperature if temperature != _DEFAULT_TEMPERATURE else float(config.get("temperature", 0.7))

    api_key = config.get("api_key") or settings.API_KEY or ""
    base_url = config.get("base_url") or settings.BASE_URL or ""
    client = _get_client(api_key, base_url)

    request_timeout = httpx.Timeout(timeout or LLM_TIMEOUT, connect=10.0)
    try:
        response = await client.chat.completions.create(
            model=effective_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=effective_max_tokens,
            temperature=effective_temperature,
            stream=False,
            timeout=request_timeout,
        )
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content
        return ""
    except httpx.TimeoutException:
        _logger.error("LLM 调用超时, timeout=%s", request_timeout)
        raise TimeoutError("AI 服务响应超时，请稍后重试")




