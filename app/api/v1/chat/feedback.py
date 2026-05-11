import logging

from fastapi import APIRouter
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success
from app.services.business import feedback_service

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.get("/feedback")
async def list_feedback(
    current_user: User = DependAuth,
):
    feedback = await feedback_service.list_feedback(current_user.username)
    return Success(data=feedback)


@router.get("/feedback/low-rating")
async def get_low_rating_feedback(
    threshold: int = 3,
    current_user: User = DependAuth,
):
    feedback = await feedback_service.get_low_rating(current_user.username, threshold)
    return Success(data=feedback)
