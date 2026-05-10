from app.services.business import memory_service

MAX_HISTORY = 20


async def save_memory(user_id: str, query: str, answer: str):
    await memory_service.save_memory(user_id, query, answer)


async def get_memory(user_id: str) -> list[tuple[str, str]]:
    return await memory_service.get_memory(user_id)


async def get_raw_history(user_id: str) -> list[dict]:
    return await memory_service.get_raw_history(user_id)


async def clear_memory(user_id: str):
    await memory_service.clear_memory(user_id)
