from app.tools.base import BaseTool
from app.utils.chat import call_llm
from app.services.business import todo_service

PRIORITY_MAP = {"高": "high", "中": "medium", "低": "low"}
PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}
CATEGORY_MAP = {"工作": "work", "学习": "study", "生活": "life", "求职": "job", "其他": "other"}
CATEGORY_LABELS = {"work": "工作", "study": "学习", "life": "生活", "job": "求职", "other": "其他"}


async def _extract_todo_fields(query: str) -> dict:
    prompt = (
        "你是一个待办任务解析助手。从用户输入中提取待办信息，以 JSON 格式输出。\n\n"
        f"用户输入：{query}\n\n"
        '输出格式：\n'
        '{\n'
        '  "content": "待办内容（简洁明了，不要照搬原句，提炼核心任务）",\n'
        '  "priority": "high/medium/low",\n'
        '  "category": "work/study/life/job/other",\n'
        '  "due_date": "截止日期，ISO格式，无则为空字符串"\n'
        '}\n\n'
        "规则：\n"
        "- content：提炼核心任务，不要原句照搬，用简洁的动宾短语描述\n"
        "- priority：包含紧急、重要、尽快等→high；一般任务→medium；不急→low\n"
        "- category：根据内容判断分类\n"
        "- due_date：提取时间信息转为ISO日期，如明天、下周一、3号等；无时间信息则为空字符串\n"
        "- 只输出 JSON，不要其他内容"
    )
    raw = await call_llm(prompt, max_tokens=300, temperature=0.1)
    return BaseTool.parse_json(raw) or {"content": query, "priority": "medium", "category": "other", "due_date": ""}


async def _generate_response(query: str, todo_item: dict) -> str:
    priority_label = PRIORITY_LABELS.get(todo_item.get("priority", "medium"), "中")
    category_label = CATEGORY_LABELS.get(todo_item.get("category", "other"), "其他")
    due = todo_item.get("due_date", "")

    prompt = (
        "你是一个智能待办助手。用户刚刚创建了一个待办任务，请用自然、友好的语气确认，不要原句照搬。\n\n"
        f"用户原始输入：{query}\n"
        f"解析后的待办：{todo_item['content']}\n"
        f"优先级：{priority_label}\n"
        f"分类：{category_label}\n"
        f"截止日期：{due or '无'}\n\n"
        "要求：\n"
        "- 用 1-2 句话自然地确认已创建待办\n"
        "- 可以适当给出相关建议或提醒\n"
        "- 语气友好、专业\n"
        "- 不要使用 markdown 格式\n"
        "- 不要原句重复用户输入"
    )
    return await call_llm(prompt, max_tokens=200, temperature=0.7)


class TodoTool(BaseTool):
    name = "todo_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = kwargs.get("user_id", "")
        if not user_id:
            raise ValueError("user_id is required")
        fields = await _extract_todo_fields(query)

        await todo_service.create_todo(
            user_id=user_id,
            content=fields.get("content") or query,
            priority=fields.get("priority", "medium"),
            category=fields.get("category", "other"),
            due_date=fields.get("due_date", ""),
        )

        todo_item = {
            "content": fields.get("content") or query,
            "priority": fields.get("priority", "medium"),
            "category": fields.get("category", "other"),
            "due_date": fields.get("due_date", ""),
        }
        return await _generate_response(query, todo_item)

    @staticmethod
    async def list_todos(user_id: str) -> str:
        todos = await todo_service.list_todos(user_id)
        if not todos:
            return "当前没有任何待办任务。"
        lines = []
        for idx, item in enumerate(todos, 1):
            status = "✅" if item.get("done") else "⬜"
            priority = PRIORITY_LABELS.get(item.get("priority", "medium"), "中")
            category = CATEGORY_LABELS.get(item.get("category", "other"), "其他")
            due = f"（截止：{item['due_date']}）" if item.get("due_date") else ""
            lines.append(f"{idx}. {status} [{priority}][{category}] {item['content']}{due}")
        return "\n".join(lines)

    @staticmethod
    async def get_todos_list(user_id: str) -> list[dict]:
        return await todo_service.list_todos(user_id)

    @staticmethod
    async def toggle_todo(item_id: int, user_id: str) -> bool:
        result = await todo_service.toggle_todo(item_id, user_id)
        return result is not None

    @staticmethod
    async def update_todo(item_id: int, user_id: str, **updates) -> bool:
        result = await todo_service.update_todo(item_id, user_id, **updates)
        return result is not None

    @staticmethod
    async def delete_todo(item_id: int, user_id: str) -> bool:
        return await todo_service.delete_todo(item_id, user_id)

    @staticmethod
    async def clear_completed(user_id: str) -> int:
        return await todo_service.clear_completed(user_id)
