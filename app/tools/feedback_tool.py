from app.tools.base import BaseTool
from app.services.business import feedback_service


class FeedbackTool(BaseTool):
    name = "feedback_tool"

    async def run(self, query: str = "", **kwargs) -> str:
        user_id = kwargs.get("user_id", "")
        if not user_id:
            raise ValueError("user_id is required")
        rating = kwargs.get("rating", "")
        comment = kwargs.get("comment", "")
        related_query = kwargs.get("related_query", "")
        related_answer = kwargs.get("related_answer", "")

        await feedback_service.create_feedback(
            user_id=user_id,
            rating=rating,
            comment=comment,
            related_query=related_query,
            related_answer=related_answer,
        )

        return f"反馈已记录：评分={rating}，意见={comment or '无'}"

    @staticmethod
    async def get_feedback_list(user_id: str) -> list[dict]:
        return await feedback_service.list_feedback(user_id)

    @staticmethod
    async def get_low_rating_feedback(threshold: int = 3, user_id: str = "") -> list[dict]:
        return await feedback_service.get_low_rating(user_id, threshold)
