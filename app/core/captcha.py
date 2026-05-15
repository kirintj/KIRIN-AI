import io
import random
import uuid
import base64

from PIL import Image, ImageDraw
from app.settings import settings

_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_client


def _random_color():
    return (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))


def _generate_images():
    width, height = 280, 150
    block_size = 40

    bg_color = _random_color()
    bg = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(bg)

    for _ in range(8):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=_random_color(), width=random.randint(1, 3))

    x = random.randint(60, width - block_size - 20)
    y = random.randint(10, height - block_size - 10)

    slider = bg.crop((x, y, x + block_size, y + block_size))

    for i in range(block_size):
        for j in range(block_size):
            px = bg.getpixel((x + i, y + j))
            darkened = tuple(max(0, c - 60) for c in px)
            bg.putpixel((x + i, y + j), darkened)

    draw.rectangle(
        [x, y, x + block_size, y + block_size],
        outline=(255, 255, 255),
        width=2,
    )

    return bg, slider, x, y


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


async def generate_captcha() -> dict:
    captcha_id = uuid.uuid4().hex
    bg, slider, x, y = _generate_images()

    redis = await get_redis()
    key = f"captcha:{captcha_id}"
    await redis.set(key, str(x), ex=settings.CAPTCHA_TTL)

    return {
        "captcha_id": captcha_id,
        "bg_image": _image_to_base64(bg),
        "slider_image": _image_to_base64(slider),
        "y_offset": y,
    }


async def verify_captcha(captcha_id: str, x: int, y: int = 0) -> bool:
    redis = await get_redis()
    key = f"captcha:{captcha_id}"
    stored = await redis.get(key)

    if stored is None:
        return False

    stored_x = int(stored.decode("utf-8") if isinstance(stored, bytes) else stored)
    await redis.delete(key)

    return abs(x - stored_x) <= settings.CAPTCHA_TOLERANCE
