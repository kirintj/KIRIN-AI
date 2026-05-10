from tortoise import fields
from .base import BaseModel, TimestampMixin


class ChatHistory(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=50, index=True, description="用户名称")
    role = fields.CharField(max_length=20, index=True, description="角色，可选值 user, assistant, system")
    content = fields.TextField(description="消息内容")
    timestamp = fields.DatetimeField(auto_now_add=True, description="创建时间")

    class Meta:
        table = "chat_history"
