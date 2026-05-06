import logging
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.tools.resume_export_tool import (
    generate_resume_data, export_docx, export_text,
    list_exports, RESUME_TEMPLATES,
)

router = APIRouter()
_logger = logging.getLogger(__name__)


class GenerateResumeRequest(BaseModel):
    user_info: str
    template: Optional[str] = "classic"


class ExportDocxRequest(BaseModel):
    resume_data: dict
    template: Optional[str] = "classic"


class ExportTextRequest(BaseModel):
    resume_data: dict


@router.get("/templates")
async def get_templates():
    return Success(data=RESUME_TEMPLATES)


@router.post("/generate")
async def generate_resume(
    request: GenerateResumeRequest,
    current_user: User = DependAuth,
):
    try:
        data = await generate_resume_data(current_user.username, request.user_info)
        return Success(data=data)
    except Exception:
        _logger.exception("生成简历数据失败")
        return Fail(code=500, msg="生成简历数据失败")


@router.post("/export/docx")
async def export_resume_docx(
    request: ExportDocxRequest,
    current_user: User = DependAuth,
):
    try:
        filepath = export_docx(current_user.username, request.resume_data, request.template or "classic")
        return FileResponse(
            filepath,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filepath.split("\\")[-1] if "\\" in filepath else filepath.split("/")[-1],
        )
    except Exception:
        _logger.exception("导出 DOCX 失败")
        return Fail(code=500, msg="导出 DOCX 失败")


@router.post("/export/text")
async def export_resume_text(
    request: ExportTextRequest,
    current_user: User = DependAuth,
):
    try:
        text = export_text(request.resume_data)
        return Success(data={"text": text})
    except Exception:
        _logger.exception("导出文本失败")
        return Fail(code=500, msg="导出文本失败")


@router.get("/exports")
async def get_export_list(
    current_user: User = DependAuth,
):
    exports = list_exports(current_user.username)
    return Success(data=exports)


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    current_user: User = DependAuth,
):
    from app.tools.resume_export_tool import RESUME_EXPORT_DIR
    filepath = RESUME_EXPORT_DIR / current_user.username / filename
    if not filepath.exists():
        return Fail(code=404, msg="文件不存在")
    return FileResponse(
        str(filepath),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )
