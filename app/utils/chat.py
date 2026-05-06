from typing import List, Dict
import httpx
from openai import AsyncOpenAI
from datetime import datetime
import json
import logging

from app.schemas.chat import ChatMessage, ChatRequest, StreamResponse
from app.settings import settings

_logger = logging.getLogger(__name__)

LLM_TIMEOUT = 120.0

async_client = AsyncOpenAI(
    api_key=settings.API_KEY,
    base_url=settings.BASE_URL,
    timeout=httpx.Timeout(LLM_TIMEOUT, connect=10.0),
)


async def get_ai_config() -> dict:
    from app.services.config import sysconfig_service
    return await sysconfig_service.get_ai_config()


def convert_messages_for_api(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


async def call_llm(prompt: str, model: str | None = None, max_tokens: int = 2000, temperature: float = 0.7, timeout: float | None = None) -> str:
    config = await get_ai_config()
    effective_model = model or config.get("model_name", settings.MODEL_NAME)
    effective_max_tokens = max_tokens if max_tokens != 2000 else int(config.get("max_tokens", 2000))
    effective_temperature = temperature if temperature != 0.7 else float(config.get("temperature", 0.7))

    request_timeout = httpx.Timeout(timeout or LLM_TIMEOUT, connect=10.0)
    try:
        response = await async_client.chat.completions.create(
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


async def generate_stream_response(request: ChatRequest, username: str):
    try:
        config = await get_ai_config()
        effective_model = request.model or config.get("model_name", settings.MODEL_NAME)

        api_messages = convert_messages_for_api(request.messages)

        stream = await async_client.chat.completions.create(
            model=effective_model,
            messages=api_messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
        )

        accumulated_content = ""

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                chunk_content = chunk.choices[0].delta.content
                accumulated_content += chunk_content

                response_data = StreamResponse(
                    content=chunk_content,
                    finished=False,
                    model=effective_model,
                    timestamp=datetime.now().isoformat(),
                )
                yield f"data: {response_data.model_dump_json()}\n\n"

        if accumulated_content:
            final_response = StreamResponse(
                content='',
                finished=True,
                model=effective_model,
                timestamp=datetime.now().isoformat(),
            )

            from app.services.chat import chat_service
            await chat_service.create_record(
                username=username,
                role="assistant",
                content=accumulated_content,
                timestamp=datetime.now(),
            )

            yield f"data: {final_response.model_dump_json()}\n\n"

    except Exception:
        _logger.exception("流式响应异常")
        error_response = {
            "error": "流式响应异常，请稍后重试",
            "finished": True,
            "timestamp": datetime.now().isoformat(),
        }
        yield f"data: {json.dumps(error_response)}\n\n"
