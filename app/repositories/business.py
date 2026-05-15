from app.core.constants import MEMORY_MAX_HISTORY, CONTENT_TRUNCATION_LENGTH
from app.models.business import TodoItem, TrackerApplication, FeedbackItem, Conversation, ConversationMessage, MemoryItem


class TodoRepository:
    def __init__(self):
        self.model = TodoItem

    async def list_by_user(self, user_id: str) -> list[TodoItem]:
        return await self.model.filter(user_id=user_id).order_by("-created_at")

    async def create(self, **kwargs) -> TodoItem:
        return await self.model.create(**kwargs)

    async def toggle(self, item_id: int, user_id: str) -> TodoItem | None:
        item = await self.model.filter(id=item_id, user_id=user_id).first()
        if not item:
            return None
        item.done = not item.done
        await item.save()
        return item

    async def update(self, item_id: int, user_id: str, **kwargs) -> TodoItem | None:
        item = await self.model.filter(id=item_id, user_id=user_id).first()
        if not item:
            return None
        allowed = {"content", "priority", "category", "due_date", "done"}
        for key in allowed & kwargs.keys():
            setattr(item, key, kwargs[key])
        await item.save()
        return item

    async def delete(self, item_id: int, user_id: str) -> bool:
        count = await self.model.filter(id=item_id, user_id=user_id).delete()
        return count > 0

    async def clear_completed(self, user_id: str) -> int:
        return await self.model.filter(user_id=user_id, done=True).delete()


class TrackerRepository:
    def __init__(self):
        self.model = TrackerApplication

    async def list_by_user(self, user_id: str, status: str | None = None) -> list[TrackerApplication]:
        qs = self.model.filter(user_id=user_id).order_by("-created_at")
        if status:
            qs = qs.filter(status=status)
        return await qs

    async def create(self, **kwargs) -> TrackerApplication:
        return await self.model.create(**kwargs)

    async def get_by_id(self, app_id: int, user_id: str) -> TrackerApplication | None:
        return await self.model.filter(id=app_id, user_id=user_id).first()

    async def update(self, app_id: int, user_id: str, **kwargs) -> TrackerApplication | None:
        app = await self.model.filter(id=app_id, user_id=user_id).first()
        if not app:
            return None
        allowed = {"company", "position", "status", "salary", "location", "source", "notes", "contact"}
        for key in allowed & kwargs.keys():
            setattr(app, key, kwargs[key])
        await app.save()
        return app

    async def delete(self, app_id: int, user_id: str) -> bool:
        count = await self.model.filter(id=app_id, user_id=user_id).delete()
        return count > 0

    async def count_by_status(self, user_id: str) -> dict:
        from tortoise.functions import Count
        rows = (
            await self.model.filter(user_id=user_id)
            .group_by("status")
            .annotate(count=Count("id"))
            .values("status", "count")
        )
        return {row["status"]: row["count"] for row in rows}

    async def total(self, user_id: str) -> int:
        return await self.model.filter(user_id=user_id).count()


class FeedbackRepository:
    def __init__(self):
        self.model = FeedbackItem

    async def list_by_user(self, user_id: str) -> list[FeedbackItem]:
        return await self.model.filter(user_id=user_id).order_by("-created_at")

    async def create(self, **kwargs) -> FeedbackItem:
        return await self.model.create(**kwargs)

    async def get_low_rating(self, user_id: str, threshold: int = 3) -> list[FeedbackItem]:
        all_items = await self.model.filter(user_id=user_id).order_by("-created_at")
        result = []
        for i in all_items:
            try:
                if int(i.rating) <= threshold:
                    result.append(i)
            except (ValueError, TypeError):
                continue
        return result


class ConversationRepository:
    def __init__(self):
        self.model = Conversation
        self.msg_model = ConversationMessage

    async def list_by_user(self, user_id: str) -> list[Conversation]:
        return await self.model.filter(user_id=user_id).order_by("-updated_at")

    async def create(self, user_id: str, title: str = "新对话") -> Conversation:
        return await self.model.create(user_id=user_id, title=title)

    async def get_by_id(self, conv_id: int, user_id: str) -> Conversation | None:
        return await self.model.filter(id=conv_id, user_id=user_id).first()

    async def rename(self, conv_id: int, user_id: str, title: str) -> Conversation | None:
        conv = await self.model.filter(id=conv_id, user_id=user_id).first()
        if not conv:
            return None
        conv.title = title
        await conv.save()
        return conv

    async def delete(self, conv_id: int, user_id: str) -> bool:
        await self.msg_model.filter(conversation_id=conv_id).delete()
        count = await self.model.filter(id=conv_id, user_id=user_id).delete()
        return count > 0

    async def get_messages(self, conv_id: int) -> list[ConversationMessage]:
        return await self.msg_model.filter(conversation_id=conv_id).order_by("created_at")

    async def add_message(self, conv_id: int, role: str, content: str) -> ConversationMessage | None:
        conv = await self.model.filter(id=conv_id).first()
        if not conv:
            return None
        msg = await self.msg_model.create(conversation_id=conv_id, role=role, content=content)
        conv.message_count = conv.message_count + 1
        if conv.message_count <= 2 and role == "user":
            conv.title = content[:CONTENT_TRUNCATION_LENGTH] + ("..." if len(content) > CONTENT_TRUNCATION_LENGTH else "")
        await conv.save()
        return msg

    async def get_recent(self, user_id: str, limit: int = 5) -> list[Conversation]:
        return await self.model.filter(user_id=user_id).order_by("-updated_at").limit(limit)


class MemoryRepository:
    def __init__(self):
        self.model = MemoryItem

    MAX_HISTORY = MEMORY_MAX_HISTORY

    async def list_by_user(self, user_id: str) -> list[MemoryItem]:
        return await self.model.filter(user_id=user_id).order_by("created_at")

    async def save(self, user_id: str, user_msg: str, assistant_msg: str) -> MemoryItem:
        item = await self.model.create(user_id=user_id, user_msg=user_msg, assistant_msg=assistant_msg)
        ids_to_keep = await (
            self.model.filter(user_id=user_id)
            .order_by("-created_at")
            .limit(self.MAX_HISTORY)
            .values_list("id", flat=True)
        )
        if ids_to_keep:
            await self.model.filter(user_id=user_id).exclude(id__in=ids_to_keep).delete()
        return item

    async def clear(self, user_id: str) -> int:
        return await self.model.filter(user_id=user_id).delete()


todo_repository = TodoRepository()
tracker_repository = TrackerRepository()
feedback_repository = FeedbackRepository()
conversation_repository = ConversationRepository()
memory_repository = MemoryRepository()
