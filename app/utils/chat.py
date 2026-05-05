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


def convert_messages_for_api(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


async def call_llm(prompt: str, model: str | None = None, max_tokens: int = 2000, temperature: float = 0.7, timeout: float | None = None) -> str:
    request_timeout = httpx.Timeout(timeout or LLM_TIMEOUT, connect=10.0)
    try:
        response = await async_client.chat.completions.create(
            model=model or settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
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
        api_messages = convert_messages_for_api(request.messages)

        stream = await async_client.chat.completions.create(
            model=request.model or settings.MODEL_NAME,
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
                    model=request.model or settings.MODEL_NAME,
                    timestamp=datetime.now().isoformat(),
                )
                yield f"data: {response_data.model_dump_json()}\n\n"

        if accumulated_content:
            final_response = StreamResponse(
                content='',
                finished=True,
                model=request.model or settings.MODEL_NAME,
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
