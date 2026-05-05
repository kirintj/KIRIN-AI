from tortoise import fields
from .base import BaseModel, TimestampMixin
from datetime import datetime

class ChatHistory(BaseModel, TimestampMixin):
    id = fields.BigIntField(pk=True, index=True, description="ID")
    username = fields.CharField(max_length=50, index=True, nullable=False, description="用户名称")
    role = fields.CharField(max_length=20, nullable=False, description="角色，可选值 user, assistant, system")
    content = fields.TextField(nullable=False, description="消息内容")
    timestamp = fields.DatetimeField(default=datetime.now, description="创建时间")
    
    class Meta:
        table = "chat_history"
