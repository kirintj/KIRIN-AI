import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.core.dependency import DependAuth
from app.models.admin import User
from app.models.business import TrackerApplication, TodoItem, Conversation
from app.schemas.base import Success
from app.services.business import tracker_service, todo_service, conversation_service
from app.tools.interview_sim_tool import list_sessions

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/overview")
async def get_dashboard_overview(current_user: User = DependAuth):
    tracker_stats = await tracker_service.get_stats(current_user.username)
    todos = await todo_service.list_todos(current_user.username)
    conversations = await conversation_service.list_conversations(current_user.username)
    interview_sessions = list_sessions(current_user.username)

    todo_done = sum(1 for t in todos if t.get("done"))
    interview_completed = sum(1 for s in interview_sessions if s.get("status") == "completed")
    interview_active = sum(1 for s in interview_sessions if s.get("status") == "active")

    avg_score = 0
    scores = [s.get("score") for s in interview_sessions if s.get("score") is not None]
    if scores:
        avg_score = round(sum(scores) / len(scores), 1)

    return Success(data={
        "tracker": tracker_stats,
        "todos": {
            "total": len(todos),
            "done": todo_done,
            "pending": len(todos) - todo_done,
        },
        "conversations": {
            "total": len(conversations),
        },
        "interviews": {
            "total": len(interview_sessions),
            "completed": interview_completed,
            "active": interview_active,
            "avg_score": avg_score,
        },
    })


@router.get("/tracker-chart")
async def get_tracker_chart(current_user: User = DependAuth):
    stats = await tracker_service.get_stats(current_user.username)
    return Success(data={
        "labels": list(stats.get("status_labels", {}).values()),
        "values": list(stats.get("by_status", {}).values()),
        "colors": list(stats.get("status_colors", {}).values()),
    })


@router.get("/weekly-activity")
async def get_weekly_activity(current_user: User = DependAuth):
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
