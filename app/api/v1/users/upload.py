import logging

from fastapi import APIRouter, UploadFile, File

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.services.upload_service import (
    save_uploaded_file,
    validate_image_type,
    validate_file_size,
    AVATAR_DIR,
    AVATAR_MAX_SIZE,
)

router = APIRouter()
_logger = logging.getLogger(__name__)


@router.post("/avatar", summary="上传头像")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = DependAuth,
):
    err = validate_image_type(file.content_type)
    if err:
        return err

    try:
        image_bytes = await file.read()

        err = validate_file_size(len(image_bytes), AVATAR_MAX_SIZE)
        if err:
            return err

        saved_name = save_uploaded_file(image_bytes, file.filename or "avatar.jpg", AVATAR_DIR, current_user.id)
        avatar_url = f"/static/avatars/{saved_name}"
        current_user.avatar = avatar_url
        await current_user.save()

        return Success(data={"avatar": avatar_url})
    except Exception:
        _logger.exception("头像上传失败")
        return Fail(code=500, msg="头像上传失败，请稍后重试")
