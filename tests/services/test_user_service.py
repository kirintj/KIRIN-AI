import pytest
from app.services.user import user_service


@pytest.mark.asyncio
async def test_get_user_by_email_not_found():
    result = await user_service.get_by_email("nonexistent@test.com")
    assert result is None
