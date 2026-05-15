from fastapi import APIRouter

from app.core.captcha import generate_captcha, verify_captcha
from app.schemas.base import Fail, Success
from app.schemas.captcha import CaptchaVerifyIn

router = APIRouter()


@router.get("/captcha/get", summary="获取滑块验证码")
async def get_captcha():
    data = await generate_captcha()
    return Success(data=data)


@router.post("/captcha/verify", summary="验证滑块验证码")
async def verify_captcha_api(req_in: CaptchaVerifyIn):
    verified = await verify_captcha(req_in.captcha_id, req_in.x)
    if not verified:
        return Fail(code=400, msg="验证码错误或已过期")
    return Success(data={"verified": True})
