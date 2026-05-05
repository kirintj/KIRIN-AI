import pytest
from app.repositories.user import user_repository


@pytest.mark.asyncio
async def test_repository_get_or_none():
    result = await user_repository.get_or_none(email="nonexistent@test.com")
    assert result is None
