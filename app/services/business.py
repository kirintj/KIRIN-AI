from app.repositories.business import (
    todo_repository,
    tracker_repository,
    feedback_repository,
    conversation_repository,
    memory_repository,
)
from app.models.business import TrackerApplication

STATUS_LIST = ["wishlist", "applied", "screening", "interview", "offer", "rejected"]
STATUS_LABELS = {
    "wishlist": "意向", "applied": "已投递", "screening": "筛选中",
    "interview": "面试中", "offer": "已录用", "rejected": "已拒绝",
}
STATUS_COLORS = {
    "wishlist": "#86909C", "applied": "#0A59F7", "screening": "#722ED1",
    "interview": "#ED6F21", "offer": "#64BB5C", "rejected": "#E84026",
}


class TodoService:
    def __init__(self):
        self.repo = todo_repository

    async def list_todos(self, user_id: str) -> list[dict]:
        items = await self.repo.list_by_user(user_id)
        return [await i.to_dict() for i in items]

    async def create_todo(self, user_id: str, **kwargs) -> dict:
        item = await self.repo.create(user_id=user_id, **kwargs)
        return await item.to_dict()

    async def toggle_todo(self, item_id: int, user_id: str) -> dict | None:
        item = await self.repo.toggle(item_id, user_id)
        return await item.to_dict() if item else None

    async def update_todo(self, item_id: int, user_id: str, **kwargs) -> dict | None:
        item = await self.repo.update(item_id, user_id, **kwargs)
        return await item.to_dict() if item else None

    async def delete_todo(self, item_id: int, user_id: str) -> bool:
        return await self.repo.delete(item_id, user_id)

    async def clear_completed(self, user_id: str) -> int:
        return await self.repo.clear_completed(user_id)


class TrackerService:
    def __init__(self):
        self.repo = tracker_repository

    async def list_applications(self, user_id: str, status: str | None = None) -> list[dict]:
        items = await self.repo.list_by_user(user_id, status)
        return [await i.to_dict() for i in items]

    async def create_application(self, user_id: str, **kwargs) -> dict:
        app = await self.repo.create(user_id=user_id, **kwargs)
        return await app.to_dict()

    async def get_application(self, app_id: int, user_id: str) -> dict | None:
        app = await self.repo.get_by_id(app_id, user_id)
        return await app.to_dict() if app else None

    async def update_application(self, app_id: int, user_id: str, **kwargs) -> dict | None:
        app = await self.repo.update(app_id, user_id, **kwargs)
        return await app.to_dict() if app else None

    async def delete_application(self, app_id: int, user_id: str) -> bool:
        return await self.repo.delete(app_id, user_id)

    async def move_application(self, app_id: int, user_id: str, new_status: str) -> dict | None:
        if new_status not in STATUS_LIST:
            return None
        return await self.update_application(app_id, user_id, status=new_status)

    async def get_stats(self, user_id: str) -> dict:
        by_status = await self.repo.count_by_status(user_id)
        total = await self.repo.total(user_id)
        stats = {s: by_status.get(s, 0) for s in STATUS_LIST}
        return {
            "total": total,
            "by_status": stats,
            "status_labels": STATUS_LABELS,
            "status_colors": STATUS_COLORS,
        }


class FeedbackService:
    def __init__(self):
        self.repo = feedback_repository

    async def list_feedback(self, user_id: str) -> list[dict]:
        items = await self.repo.list_by_user(user_id)
        return [await i.to_dict() for i in items]

    async def create_feedback(self, user_id: str, **kwargs) -> dict:
        item = await self.repo.create(user_id=user_id, **kwargs)
        return await item.to_dict()

    async def get_low_rating(self, user_id: str, threshold: int = 3) -> list[dict]:
        items = await self.repo.get_low_rating(user_id, threshold)
        return [await i.to_dict() for i in items]


class ConversationService:
    def __init__(self):
        self.repo = conversation_repository

    async def list_conversations(self, user_id: str) -> list[dict]:
        convs = await self.repo.list_by_user(user_id)
        return [await c.to_dict() for c in convs]

    async def create_conversation(self, user_id: str, title: str = "新对话") -> dict:
        conv = await self.repo.create(user_id, title)
        return await conv.to_dict()

    async def rename_conversation(self, conv_id: int, user_id: str, title: str) -> dict | None:
        conv = await self.repo.rename(conv_id, user_id, title)
        return await conv.to_dict() if conv else None

    async def delete_conversation(self, conv_id: int, user_id: str) -> bool:
        return await self.repo.delete(conv_id, user_id)

    async def get_messages(self, conv_id: int) -> list[dict]:
        msgs = await self.repo.get_messages(conv_id)
        return [await m.to_dict() for m in msgs]

    async def add_message(self, conv_id: int, role: str, content: str) -> dict | None:
        msg = await self.repo.add_message(conv_id, role, content)
        return await msg.to_dict() if msg else None

    async def get_recent(self, user_id: str, limit: int = 5) -> list[dict]:
        convs = await self.repo.get_recent(user_id, limit)
        return [await c.to_dict() for c in convs]


class MemoryService:
    def __init__(self):
        self.repo = memory_repository

    async def get_memory(self, user_id: str) -> list[tuple[str, str]]:
        items = await self.repo.list_by_user(user_id)
        return [(i.user_msg, i.assistant_msg) for i in items]

    async def get_raw_history(self, user_id: str) -> list[dict]:
        items = await self.repo.list_by_user(user_id)
        return [{"user": i.user_msg, "assistant": i.assistant_msg} for i in items]

    async def save_memory(self, user_id: str, query: str, answer: str):
        await self.repo.save(user_id, query, answer)

    async def clear_memory(self, user_id: str) -> int:
        return await self.repo.clear(user_id)


todo_service = TodoService()
tracker_service = TrackerService()
feedback_service = FeedbackService()
conversation_service = ConversationService()
memory_service = MemoryService()
