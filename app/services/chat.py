
from app.repositories.chat import chat_repository


class ChatService:
    def __init__(self):
        self.repo = chat_repository

    async def get_history_by_username(self, username: str):
        return await self.repo.get_by_username(username)

    async def clear_history_by_username(self, username: str) -> int:
        return await self.repo.delete_by_username(username)

    async def create_record(self, **kwargs):
        return await self.repo.create_record(**kwargs)


chat_service = ChatService()
