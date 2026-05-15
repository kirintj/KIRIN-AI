import random
import uuid

from app.settings import settings

_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis

        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_client


async def generate_captcha() -> dict:
    captcha_id = uuid.uuid4().hex
    # Generate random gap position (x coordinate in pixels)
    # Component default: w=310, l=42, r=10, so valid range is ~62 to ~248
    x = random.randint(80, 230)

    redis = await get_redis()
    key = f"captcha:{captcha_id}"
    await redis.set(key, str(x), ex=settings.CAPTCHA_TTL)

    return {
        "captcha_id": captcha_id,
        "x": x,
    }


async def verify_captcha(captcha_id: str, x: int) -> bool:
    redis = await get_redis()
    key = f"captcha:{captcha_id}"
    stored = await redis.get(key)

    if stored is None:
        return False

    stored_x = int(stored.decode("utf-8") if isinstance(stored, bytes) else stored)
    await redis.delete(key)

    return abs(x - stored_x) <= settings.CAPTCHA_TOLERANCE
