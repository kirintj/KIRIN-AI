import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.tools.base import BaseTool
from app.utils.chat import call_llm

TODO_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "todos.json"

PRIORITY_MAP = {"高": "high", "中": "medium", "低": "low"}
PRIORITY_LABELS = {"high": "高", "medium": "中", "low": "低"}
CATEGORY_MAP = {"工作": "work", "学习": "study", "生活": "life", "求职": "job", "其他": "other"}
CATEGORY_LABELS = {"work": "工作", "study": "学习", "life": "生活", "job": "求职", "other": "其他"}


def _ensure_file():
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TODO_FILE.exists():
        TODO_FILE.write_text("{}", encoding="utf-8")


def _load_all_todos() -> dict:
    _ensure_file()
    data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        TODO_FILE.write_text("{}", encoding="utf-8")
        return {}
    return data


def _save_all_todos(all_todos: dict):
    _ensure_file()
    TODO_FILE.write_text(json.dumps(all_todos, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_user_todos(user_id: str) -> list:
    all_todos = _load_all_todos()
    return all_todos.get(user_id, [])


def _set_user_todos(user_id: str, todos: list):
    all_todos = _load_all_todos()
    all_todos[user_id] = todos
    _save_all_todos(all_todos)


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
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except (json.JSONDecodeError, AttributeError):
        return {"content": query, "priority": "medium", "category": "other", "due_date": ""}


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
        user_id = kwargs.get("user_id", "default")
        fields = await _extract_todo_fields(query)

        todo_item = {
            "content": fields.get("content") or query,
            "priority": fields.get("priority", "medium"),
            "category": fields.get("category", "other"),
            "due_date": fields.get("due_date", ""),
            "created_at": datetime.now().isoformat(),
            "done": False,
        }

        todos = _get_user_todos(user_id)
        todos.append(todo_item)
        _set_user_todos(user_id, todos)

        response = await _generate_response(query, todo_item)
        return response

    @staticmethod
    async def list_todos(user_id: str = "default") -> str:
        todos = _get_user_todos(user_id)
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
    def get_todos_list(user_id: str = "default") -> list[dict]:
        return _get_user_todos(user_id)

    @staticmethod
    def toggle_todo(index: int, user_id: str = "default") -> bool:
        todos = _get_user_todos(user_id)
        if 0 <= index < len(todos):
            todos[index]["done"] = not todos[index].get("done", False)
            _set_user_todos(user_id, todos)
            return True
        return False

    @staticmethod
    def update_todo(index: int, user_id: str = "default", **updates) -> bool:
        todos = _get_user_todos(user_id)
        if 0 <= index < len(todos):
            allowed = {"content", "priority", "category", "due_date"}
            for key in allowed & updates.keys():
                todos[index][key] = updates[key]
            _set_user_todos(user_id, todos)
            return True
        return False

    @staticmethod
    def delete_todo(index: int, user_id: str = "default") -> bool:
        todos = _get_user_todos(user_id)
        if 0 <= index < len(todos):
            todos.pop(index)
            _set_user_todos(user_id, todos)
            return True
        return False

    @staticmethod
    def clear_completed(user_id: str = "default") -> int:
        todos = _get_user_todos(user_id)
        remaining = [t for t in todos if not t.get("done")]
        removed = len(todos) - len(remaining)
        _set_user_todos(user_id, remaining)
        return removed
