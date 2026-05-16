import logging
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Form
from openai import APIError as OpenAIAPIError
from openai import BadRequestError as OpenAIBadRequestError

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
    "interview": "activity-source",
    "salary": "salary",
    "guide": "map-draw",
}


@router.post("", summary="上传文档到知识库（支持PDF/DOCX/TXT等）")
async def upload_documents(
    files: List[UploadFile] = File(...),
    collection: str = Form("knowledge_base"),
    doc_type: str = Form(""),
    current_user: User = DependAuth,
):
    if not files:
        return Fail(code=400, msg="请选择要上传的文件")

    collection_name = COLLECTION_MAP.get(collection, collection)

    all_documents = []
    all_doc_ids = []
    valid_count = 0
    skipped_reasons = []

    for file in files:
        if not file.filename:
            skipped_reasons.append("文件名为空")
            continue

        err = validate_file_extension(file.filename)
        if err:
            skipped_reasons.append(f"{file.filename}: {err.msg}")
            continue

        content = await file.read()

        err = validate_file_size(len(content), DEFAULT_MAX_SIZE)
        if err:
            skipped_reasons.append(f"{file.filename}: {err.msg}")
            continue

        documents = extract_text_from_file(file.filename, content)

        if documents:
            file_prefix = f"upload_{current_user.id}_{uuid.uuid4().hex[:8]}"
            for page_idx, _ in enumerate(documents):
                all_doc_ids.append(f"{file_prefix}_p{page_idx}")
            all_documents.extend(documents)
            valid_count += 1
            save_uploaded_file(content, file.filename, UPLOAD_DIR, current_user.id)
        else:
            skipped_reasons.append(f"{file.filename}: 无法提取文本内容")

    if not all_documents:
        detail = "; ".join(skipped_reasons) if skipped_reasons else "未提供有效文件"
        return Fail(code=400, msg=f"没有有效的文件内容: {detail}")

    try:
        source = f"upload_{current_user.username}"
        await add_documents(
            all_documents,
            doc_ids=all_doc_ids,
            collection_name=collection_name,
            source=source,
            doc_type=doc_type,
            user_id=current_user.id,
        )
        return Success(data={
            "message": f"成功上传 {valid_count} 个文件到知识库集合 [{collection_name}]",
            "count": valid_count,
            "collection": collection_name,
        })
    except OpenAIBadRequestError:
        _logger.exception("文件上传失败: 向量模型参数错误")
        return Fail(code=400, msg="向量模型参数错误，请检查文件内容")
    except OpenAIAPIError:
        _logger.exception("文件上传失败: 向量模型调用异常")
        return Fail(code=502, msg="向量模型服务异常，请稍后重试")
    except Exception:
        _logger.exception("文件上传失败")
        return Fail(code=500, msg="文件上传失败，请稍后重试")
