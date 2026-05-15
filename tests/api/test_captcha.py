import pytest
from unittest.mock import AsyncMock, patch
from app.core.captcha import generate_captcha, verify_captcha


@pytest.mark.asyncio
async def test_generate_captcha_returns_expected_fields():
    with patch("app.core.captcha.get_redis") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        result = await generate_captcha()
        assert "captcha_id" in result
        assert "bg_image" in result
        assert "slider_image" in result
        assert "y_offset" in result
        assert isinstance(result["captcha_id"], str)
        assert isinstance(result["bg_image"], str)
        assert isinstance(result["slider_image"], str)
        assert isinstance(result["y_offset"], int)


@pytest.mark.asyncio
async def test_verify_captcha_correct():
    with patch("app.core.captcha.get_redis") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"100"
        mock_get_redis.return_value = mock_redis
        result = await verify_captcha("test-id", 102, 0)
        assert result is True
        mock_redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_verify_captcha_wrong():
    with patch("app.core.captcha.get_redis") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = b"100"
        mock_get_redis.return_value = mock_redis
        result = await verify_captcha("test-id", 200, 0)
        assert result is False


@pytest.mark.asyncio
async def test_verify_captcha_expired():
    with patch("app.core.captcha.get_redis") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_get_redis.return_value = mock_redis
        result = await verify_captcha("test-id", 100, 0)
        assert result is False
