from app.services.business import conversation_service


async def create_conversation(user_id: str, title: str = "新对话") -> dict:
    return await conversation_service.create_conversation(user_id, title)


async def list_conversations(user_id: str) -> list[dict]:
    return await conversation_service.list_conversations(user_id)


async def get_conversation(conv_id: int, user_id: str) -> dict | None:
    return await conversation_service.get_messages_if_owner(conv_id, user_id)


async def rename_conversation(conv_id: int, user_id: str, title: str) -> bool:
    result = await conversation_service.rename_conversation(conv_id, user_id, title)
    return result is not None


async def delete_conversation(conv_id: int, user_id: str) -> bool:
    return await conversation_service.delete_conversation(conv_id, user_id)


async def get_messages(conv_id: int) -> list[dict]:
    return await conversation_service.get_messages(conv_id)


async def add_message(conv_id: int, role: str, content: str) -> bool:
    result = await conversation_service.add_message(conv_id, role, content)
    return result is not None


async def get_recent_conversations(user_id: str, limit: int = 5) -> list[dict]:
    return await conversation_service.get_recent(user_id, limit)
