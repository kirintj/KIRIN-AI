import json
from datetime import datetime
from pathlib import Path

from app.tools.base import BaseTool

FEEDBACK_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "feedback.json"


def _ensure_file():
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not FEEDBACK_FILE.exists():
        FEEDBACK_FILE.write_text("{}", encoding="utf-8")


def _load_all_feedback() -> dict:
    _ensure_file()
    return json.loads(FEEDBACK_FILE.read_text(encoding="utf-8"))


def _save_all_feedback(all_feedback: dict):
    _ensure_file()
    FEEDBACK_FILE.write_text(
        json.dumps(all_feedback, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _get_user_feedback(user_id: str) -> list:
    all_feedback = _load_all_feedback()
    return all_feedback.get(user_id, [])


def _set_user_feedback(user_id: str, feedback_list: list):
    all_feedback = _load_all_feedback()
    all_feedback[user_id] = feedback_list
    _save_all_feedback(all_feedback)


class FeedbackTool(BaseTool):
    name = "feedback_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = kwargs.get("user_id", "default")
        rating = kwargs.get("rating", "")
        comment = kwargs.get("comment", "")
        related_query = kwargs.get("related_query", "")
        related_answer = kwargs.get("related_answer", "")

        feedback_list = _get_user_feedback(user_id)
        feedback_item = {
            "rating": rating,
            "comment": comment,
            "related_query": related_query,
            "related_answer": related_answer,
            "created_at": datetime.now().isoformat(),
        }
        feedback_list.append(feedback_item)
        _set_user_feedback(user_id, feedback_list)

        return f"反馈已记录：评分={rating}，意见={comment or '无'}"

    @staticmethod
    def get_feedback_list(user_id: str = "default") -> list[dict]:
        return _get_user_feedback(user_id)

    @staticmethod
    def get_low_rating_feedback(threshold: int = 3, user_id: str = "default") -> list[dict]:
        feedback_list = _get_user_feedback(user_id)
        return [
            item for item in feedback_list
            if item.get("rating", "").isdigit() and int(item["rating"]) <= threshold
        ]
