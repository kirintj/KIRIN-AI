from tortoise import fields
from .base import BaseModel, TimestampMixin


class TodoItem(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=50, index=True, description="用户标识")
    content = fields.TextField(description="待办内容")
    priority = fields.CharField(max_length=10, default="medium", description="优先级: high/medium/low")
    category = fields.CharField(max_length=20, default="other", description="分类: work/study/life/job/other")
    due_date = fields.CharField(max_length=20, default="", description="截止日期")
    done = fields.BooleanField(default=False, description="是否完成")

    class Meta:
        table = "todo_item"


class TrackerApplication(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=50, index=True, description="用户标识")
    company = fields.CharField(max_length=100, default="", description="公司名称")
    position = fields.CharField(max_length=100, default="", description="职位名称")
    status = fields.CharField(max_length=20, default="applied", index=True, description="状态")
    salary = fields.CharField(max_length=50, default="", description="薪资范围")
    location = fields.CharField(max_length=50, default="", description="工作地点")
    source = fields.CharField(max_length=50, default="", description="投递渠道")
    notes = fields.TextField(default="", description="备注")
    contact = fields.CharField(max_length=100, default="", description="联系人")

    class Meta:
        table = "tracker_application"


class FeedbackItem(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=50, index=True, description="用户标识")
    rating = fields.CharField(max_length=10, default="", description="评分")
    comment = fields.TextField(default="", description="意见")
    related_query = fields.TextField(default="", description="关联问题")
    related_answer = fields.TextField(default="", description="关联回答")

    class Meta:
        table = "feedback_item"


class Conversation(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=50, index=True, description="用户标识")
    title = fields.CharField(max_length=200, default="新对话", description="对话标题")
    message_count = fields.IntField(default=0, description="消息数量")

    class Meta:
        table = "conversation"


class ConversationMessage(BaseModel, TimestampMixin):
    conversation = fields.ForeignKeyField("models.Conversation", related_name="messages", description="所属对话")
    role = fields.CharField(max_length=20, description="角色: user/assistant/system")
    content = fields.TextField(description="消息内容")

    class Meta:
        table = "conversation_message"


class MemoryItem(BaseModel, TimestampMixin):
    user_id = fields.CharField(max_length=50, index=True, description="用户标识")
    user_msg = fields.TextField(description="用户消息")
    assistant_msg = fields.TextField(description="助手回复")

    class Meta:
        table = "memory_item"
