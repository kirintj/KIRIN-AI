import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.core.dependency import DependAuth
from app.models.admin import User
from app.models.business import TrackerApplication, Conversation
from app.schemas.base import Success
from app.services.business import tracker_service, todo_service, conversation_service
from app.tools.interview_sim_tool import list_sessions

router = APIRouter()
_logger = logging.getLogger(__name__)


async def _safe_tracker_stats(user_id: str) -> dict:
    try:
        return await tracker_service.get_stats(user_id)
    except Exception as e:
        _logger.warning("Dashboard: tracker_stats failed: %s", e)
        return {"total": 0, "by_status": {}, "status_labels": {}, "status_colors": {}}


async def _safe_todo_stats(user_id: str) -> dict:
    try:
        todos = await todo_service.list_todos(user_id)
        done = sum(1 for t in todos if t.get("done"))
        return {"total": len(todos), "done": done, "pending": len(todos) - done}
    except Exception as e:
        _logger.warning("Dashboard: todo_stats failed: %s", e)
        return {"total": 0, "done": 0, "pending": 0}


async def _safe_conversation_count(user_id: str) -> dict:
    try:
        convs = await conversation_service.list_conversations(user_id)
        return {"total": len(convs)}
    except Exception as e:
        _logger.warning("Dashboard: conversation_count failed: %s", e)
        return {"total": 0}


def _safe_interview_stats(user_id: str) -> dict:
    try:
        sessions = list_sessions(user_id)
        completed = sum(1 for s in sessions if s.get("status") == "completed")
        active = sum(1 for s in sessions if s.get("status") == "active")
        scores = [s.get("score") for s in sessions if s.get("score") is not None]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0
        return {"total": len(sessions), "completed": completed, "active": active, "avg_score": avg_score}
    except Exception as e:
        _logger.warning("Dashboard: interview_stats failed: %s", e)
        return {"total": 0, "completed": 0, "active": 0, "avg_score": 0}


@router.get("/overview")
async def get_dashboard_overview(current_user: User = DependAuth):
    tracker_stats = await _safe_tracker_stats(current_user.username)
    todo_stats = await _safe_todo_stats(current_user.username)
    conv_stats = await _safe_conversation_count(current_user.username)
    interview_stats = _safe_interview_stats(current_user.username)

    return Success(data={
        "tracker": tracker_stats,
        "todos": todo_stats,
        "conversations": conv_stats,
        "interviews": interview_stats,
    })


@router.get("/tracker-chart")
async def get_tracker_chart(current_user: User = DependAuth):
    stats = await _safe_tracker_stats(current_user.username)
    return Success(data={
        "labels": list(stats.get("status_labels", {}).values()),
        "values": list(stats.get("by_status", {}).values()),
        "colors": list(stats.get("status_colors", {}).values()),
    })


@router.get("/weekly-activity")
async def get_weekly_activity(current_user: User = DependAuth):
    try:
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today - timedelta(days=6)

        apps = await TrackerApplication.filter(
            user_id=current_user.username, created_at__gte=week_ago
        ).values_list("created_at", flat=True)
        convs = await Conversation.filter(
            user_id=current_user.username, created_at__gte=week_ago
        ).values_list("created_at", flat=True)

        days = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime("%m-%d")
            day_start = day
            day_end = day + timedelta(days=1)

            app_count = sum(1 for a in apps if a and day_start <= a.replace(tzinfo=timezone.utc) < day_end)
            conv_count = sum(1 for c in convs if c and day_start <= c.replace(tzinfo=timezone.utc) < day_end)
            days.append({
                "date": day_str,
                "count": app_count + conv_count,
                "applications": app_count,
                "conversations": conv_count,
            })
        return Success(data=days)
    except Exception as e:
        _logger.warning("Dashboard: weekly_activity failed: %s", e)
        now = datetime.now(timezone.utc)
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return Success(data=[
            {"date": (today - timedelta(days=i)).strftime("%m-%d"), "count": 0, "applications": 0, "conversations": 0}
            for i in range(6, -1, -1)
        ])

