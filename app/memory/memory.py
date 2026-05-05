import json
from pathlib import Path
from datetime import datetime

MEMORY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "memory"

MAX_HISTORY = 20


def _get_user_file(user_id: str) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    return MEMORY_DIR / f"{user_id}.json"


def _load_history(user_id: str) -> list[dict]:
    file_path = _get_user_file(user_id)
    if not file_path.exists():
        return []
    return json.loads(file_path.read_text(encoding="utf-8"))


def _save_history(user_id: str, history: list[dict]):
    file_path = _get_user_file(user_id)
    file_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def save_memory(user_id: str, query: str, answer: str):
    """保存一轮对话到用户的历史记录"""
    history = _load_history(user_id)
    history.append({
        "user": query,
        "assistant": answer,
        "timestamp": datetime.now().isoformat(),
    })
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    _save_history(user_id, history)


def get_memory(user_id: str) -> list[tuple[str, str]]:
    """获取用户的对话历史，返回 (user, assistant) 元组列表"""
    history = _load_history(user_id)
    return [(item["user"], item["assistant"]) for item in history]


def get_raw_history(user_id: str) -> list[dict]:
    """获取用户原始对话历史，保留完整字段"""
    return _load_history(user_id)


def clear_memory(user_id: str):
    """清空用户的对话历史"""
    file_path = _get_user_file(user_id)
    if file_path.exists():
        file_path.write_text("[]", encoding="utf-8")
