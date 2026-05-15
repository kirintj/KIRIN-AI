from pydantic import BaseModel, Field


class CaptchaVerifyIn(BaseModel):
    captcha_id: str = Field(..., description="验证码ID")
    x: int = Field(..., description="滑块x坐标")
    y: int = Field(0, description="滑块y坐标")
