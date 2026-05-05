import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, Form
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.rag.chromadb_client import add_documents
from app.services.upload_service import (
    extract_text_from_file,
    save_uploaded_file,
    validate_file_extension,
    validate_file_size,
    UPLOAD_DIR,
    DEFAULT_MAX_SIZE,
)

router = APIRouter()
_logger = logging.getLogger(__name__)

COLLECTION_MAP = {
    "resume": "resume",
    "interview": "interview",
    "salary": "salary",
    "guide": "guide",
}


@router.post("/", summary="上传文档到知识库（支持PDF/DOCX/TXT等）")
async def upload_documents(
    files: List[UploadFile] = File(...),
    collection: str = Form("knowledge_base"),
    doc_type: str = Form(""),
    current_user: User = DependAuth,
):
    if not files:
        return Fail(code=400, msg="请选择要上传的文件")

    collection_name = COLLECTION_MAP.get(collection, collection)

    try:
        all_documents = []
        valid_count = 0

        for file in files:
            if not file.filename:
                continue

            err = validate_file_extension(file.filename)
            if err:
                continue

            content = await file.read()

            err = validate_file_size(len(content), DEFAULT_MAX_SIZE)
            if err:
                continue

            documents = extract_text_from_file(file.filename, content)

            if documents:
                all_documents.extend(documents)
                valid_count += 1
                save_uploaded_file(content, file.filename, UPLOAD_DIR, current_user.id)

        if all_documents:
            source = f"upload_{current_user.username}"
            await add_documents(
                all_documents,
                collection_name=collection_name,
                source=source,
                doc_type=doc_type,
            )
            return Success(data={
                "message": f"成功上传 {valid_count} 个文件到知识库集合 [{collection_name}]",
                "count": valid_count,
                "collection": collection_name,
            })
        else:
            return Fail(code=400, msg="没有有效的文件内容，支持格式：PDF/DOCX/TXT/MD等")

    except Exception:
        _logger.exception("文件上传失败")
        return Fail(code=500, msg="文件上传失败，请稍后重试")
