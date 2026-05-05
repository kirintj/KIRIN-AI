import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.tools.base import BaseTool
from app.utils.chat import call_llm

TRACKER_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "tracker"

STATUS_LIST = ["wishlist", "applied", "screening", "interview", "offer", "rejected"]
STATUS_LABELS = {
    "wishlist": "意向",
    "applied": "已投递",
    "screening": "筛选中",
    "interview": "面试中",
    "offer": "已录用",
    "rejected": "已拒绝",
}
STATUS_COLORS = {
    "wishlist": "#86909C",
    "applied": "#0A59F7",
    "screening": "#722ED1",
    "interview": "#ED6F21",
    "offer": "#64BB5C",
    "rejected": "#E84026",
}


def _ensure_dir(user_id: str) -> Path:
    user_dir = TRACKER_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def _get_tracker_path(user_id: str) -> Path:
    return _ensure_dir(user_id) / "applications.json"


def _load_applications(user_id: str) -> list[dict]:
    path = _get_tracker_path(user_id)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return data


def _save_applications(user_id: str, apps: list[dict]):
    path = _get_tracker_path(user_id)
    path.write_text(json.dumps(apps, ensure_ascii=False, indent=2), encoding="utf-8")


def create_application(user_id: str, data: dict) -> dict:
    apps = _load_applications(user_id)
    app_id = f"app_{len(apps) + 1:04d}_{datetime.now().strftime('%m%d%H%M')}"
    now = datetime.now().isoformat()
    application = {
        "id": app_id,
        "company": data.get("company", ""),
        "position": data.get("position", ""),
        "status": data.get("status", "applied"),
        "salary": data.get("salary", ""),
        "location": data.get("location", ""),
        "source": data.get("source", ""),
        "notes": data.get("notes", ""),
        "contact": data.get("contact", ""),
        "created_at": now,
        "updated_at": now,
    }
    apps.insert(0, application)
    _save_applications(user_id, apps)
    return application


def list_applications(user_id: str, status: Optional[str] = None) -> list[dict]:
    apps = _load_applications(user_id)
    if status:
        apps = [a for a in apps if a.get("status") == status]
    return apps


def get_application(user_id: str, app_id: str) -> Optional[dict]:
    apps = _load_applications(user_id)
    for app in apps:
        if app["id"] == app_id:
            return app
    return None


def update_application(user_id: str, app_id: str, updates: dict) -> bool:
    apps = _load_applications(user_id)
    for app in apps:
        if app["id"] == app_id:
            allowed = {"company", "position", "status", "salary", "location", "source", "notes", "contact"}
            for key in allowed & updates.keys():
                app[key] = updates[key]
            app["updated_at"] = datetime.now().isoformat()
            _save_applications(user_id, apps)
            return True
    return False


def delete_application(user_id: str, app_id: str) -> bool:
    apps = _load_applications(user_id)
    new_apps = [a for a in apps if a["id"] != app_id]
    if len(new_apps) == len(apps):
        return False
    _save_applications(user_id, new_apps)
    return True


def move_application(user_id: str, app_id: str, new_status: str) -> bool:
    if new_status not in STATUS_LIST:
        return False
    return update_application(user_id, app_id, {"status": new_status})


def get_tracker_stats(user_id: str) -> dict:
    apps = _load_applications(user_id)
    stats = {s: 0 for s in STATUS_LIST}
    for app in apps:
        status = app.get("status", "applied")
        if status in stats:
            stats[status] += 1
    return {
        "total": len(apps),
        "by_status": stats,
        "status_labels": STATUS_LABELS,
        "status_colors": STATUS_COLORS,
    }


async def _extract_application_fields(query: str) -> dict:
    prompt = (
        "你是一个求职信息解析助手。从用户输入中提取求职申请信息，以 JSON 格式输出。\n\n"
        f"用户输入：{query}\n\n"
        '输出格式：\n'
        '{\n'
        '  "company": "公司名称",\n'
        '  "position": "职位名称",\n'
        '  "status": "wishlist/applied/screening/interview/offer/rejected",\n'
        '  "salary": "薪资范围，无则为空字符串",\n'
        '  "location": "工作地点，无则为空字符串",\n'
        '  "source": "投递渠道，如Boss直聘、拉勾等，无则为空字符串",\n'
        '  "notes": "备注信息",\n'
        '  "contact": "联系人信息，无则为空字符串"\n'
        '}\n\n'
        "状态映射规则：\n"
        "- 想投/意向/考虑中 → wishlist\n"
        "- 已投递/已申请/投了 → applied\n"
        "- 筛选中/评估中/简历审核 → screening\n"
        "- 面试中/约面试/二面/三面 → interview\n"
        "- 录用/offer/入职 → offer\n"
        "- 拒绝/没过/挂了 → rejected\n\n"
        "- 只输出 JSON，不要其他内容"
    )
    raw = await call_llm(prompt, max_tokens=400, temperature=0.1)
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
        return {"company": "", "position": "", "status": "applied"}


async def _generate_tracker_response(query: str, app_data: dict) -> str:
    status_label = STATUS_LABELS.get(app_data.get("status", "applied"), "已投递")
    prompt = (
        "你是一个智能求职助手。用户刚刚添加了一条求职记录，请用自然、友好的语气确认。\n\n"
        f"用户原始输入：{query}\n"
        f"公司：{app_data.get('company', '未知')}\n"
        f"职位：{app_data.get('position', '未知')}\n"
        f"状态：{status_label}\n"
        f"薪资：{app_data.get('salary', '未填写')}\n"
        f"地点：{app_data.get('location', '未填写')}\n\n"
        "要求：\n"
        "- 用 1-2 句话自然地确认已添加记录\n"
        "- 可以适当给出求职建议或提醒\n"
        "- 语气友好、专业\n"
        "- 不要使用 markdown 格式"
    )
    return await call_llm(prompt, max_tokens=200, temperature=0.7)


class TrackerTool(BaseTool):
    name = "tracker_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = kwargs.get("user_id", "default")
        fields = await _extract_application_fields(query)
        app_data = create_application(user_id, fields)
        return await _generate_tracker_response(query, app_data)

    @staticmethod
    async def list_apps(user_id: str = "default") -> str:
        apps = list_applications(user_id)
        if not apps:
            return "当前没有任何求职记录。"
        lines = []
        for app in apps:
            status = STATUS_LABELS.get(app.get("status", "applied"), "未知")
            lines.append(f"- {app.get('company', '未知')} | {app.get('position', '未知')} | {status}")
        return "\n".join(lines)
