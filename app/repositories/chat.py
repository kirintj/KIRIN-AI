from app.models.chat import ChatHistory
from app.repositories.base import RepositoryBase


class ChatRepository:
    def __init__(self):
        self.model = ChatHistory

    async def get_by_username(self, username: str):
        return await self.model.filter(username=username).order_by("timestamp")

    async def delete_by_username(self, username: str) -> int:
        return await self.model.filter(username=username).delete()

    async def create_record(self, **kwargs) -> ChatHistory:
        return await self.model.create(**kwargs)


chat_repository = ChatRepository()
