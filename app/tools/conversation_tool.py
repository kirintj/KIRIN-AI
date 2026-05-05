import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

CONVERSATIONS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "conversations"


def _ensure_dir(user_id: str) -> Path:
    user_dir = CONVERSATIONS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def _get_meta_path(user_id: str) -> Path:
    return _ensure_dir(user_id) / "meta.json"


def _get_conv_path(user_id: str, conv_id: str) -> Path:
    return _ensure_dir(user_id) / f"{conv_id}.json"


def _load_meta(user_id: str) -> list[dict]:
    path = _get_meta_path(user_id)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_meta(user_id: str, meta: list[dict]):
    path = _get_meta_path(user_id)
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_messages(user_id: str, conv_id: str) -> list[dict]:
    path = _get_conv_path(user_id, conv_id)
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _save_messages(user_id: str, conv_id: str, messages: list[dict]):
    path = _get_conv_path(user_id, conv_id)
    path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")


def create_conversation(user_id: str, title: str = "新对话") -> dict:
    conv_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    conv_meta = {
        "id": conv_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "message_count": 0,
    }
    meta = _load_meta(user_id)
    meta.insert(0, conv_meta)
    _save_meta(user_id, meta)
    _save_messages(user_id, conv_id, [])
    return conv_meta


def list_conversations(user_id: str) -> list[dict]:
    return _load_meta(user_id)


def get_conversation(user_id: str, conv_id: str) -> Optional[dict]:
    meta = _load_meta(user_id)
    for item in meta:
        if item["id"] == conv_id:
            return item
    return None


def rename_conversation(user_id: str, conv_id: str, title: str) -> bool:
    meta = _load_meta(user_id)
    for item in meta:
        if item["id"] == conv_id:
            item["title"] = title
            item["updated_at"] = datetime.now().isoformat()
            _save_meta(user_id, meta)
            return True
    return False


def delete_conversation(user_id: str, conv_id: str) -> bool:
    meta = _load_meta(user_id)
    new_meta = [item for item in meta if item["id"] != conv_id]
    if len(new_meta) == len(meta):
        return False
    _save_meta(user_id, new_meta)
    conv_path = _get_conv_path(user_id, conv_id)
    if conv_path.exists():
        conv_path.unlink()
    return True


def get_messages(user_id: str, conv_id: str) -> list[dict]:
    return _load_messages(user_id, conv_id)


def add_message(user_id: str, conv_id: str, role: str, content: str) -> bool:
    messages = _load_messages(user_id, conv_id)
    messages.append({
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
    })
    _save_messages(user_id, conv_id, messages)
    meta = _load_meta(user_id)
    for item in meta:
        if item["id"] == conv_id:
            item["updated_at"] = datetime.now().isoformat()
            item["message_count"] = len(messages)
            if len(messages) <= 2 and role == "user":
                title = content[:30] + ("..." if len(content) > 30 else "")
                item["title"] = title
            _save_meta(user_id, meta)
            return True
    return True


def get_recent_conversations(user_id: str, limit: int = 5) -> list[dict]:
    meta = _load_meta(user_id)
    return meta[:limit]
