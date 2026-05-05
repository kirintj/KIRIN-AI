import logging
from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.rag.chromadb_client import (
    add_documents,
    search_chromadb,
    search_with_filter,
    hybrid_search,
    get_collection_stats,
    list_documents,
    get_document_chunks,
    delete_all_documents,
    rebuild_all_collections,
    COLLECTION_NAMES,
)
from app.rag.pipeline import AdvancedRAGPipeline, PipelineConfig

router = APIRouter()
_logger = logging.getLogger(__name__)


class AddDocumentInput(BaseModel):
    content: str
    collection: str = "knowledge_base"
    source: str = ""
    doc_type: str = ""


class SearchInput(BaseModel):
    query: str
    collection: str = "knowledge_base"
    top_k: int = 5
    doc_type: str = ""
    source: str = ""


class AdvancedSearchInput(BaseModel):
    query: str
    collection: str = ""
    top_k: int = 5
    enable_query_rewrite: bool = True
    enable_rerank: bool = True
    enable_hybrid_search: bool = True
    enable_context_compress: bool = False
    doc_type: str = ""
    source: str = ""


@router.post("/add", summary="添加文档到知识库")
async def add_document_api(
    data: AddDocumentInput,
    current_user: User = DependAuth,
):
    try:
        await add_documents(
            [data.content],
            collection_name=data.collection,
            source=data.source or f"manual_{current_user.username}",
            doc_type=data.doc_type,
        )
        return Success(data={"message": f"文档已添加到集合 [{data.collection}]"})
    except Exception:
        _logger.exception("添加文档失败")
        return Fail(code=500, msg="添加文档失败")


@router.post("/search", summary="基础向量检索")
async def search_api(
    data: SearchInput,
    current_user: User = DependAuth,
):
    try:
        if data.doc_type or data.source:
            docs = await search_with_filter(
                data.query, top_k=data.top_k,
                collection_name=data.collection,
                doc_type=data.doc_type, source=data.source,
            )
        else:
            docs = await search_chromadb(data.query, top_k=data.top_k, collection_name=data.collection)
        return Success(data={"results": docs, "count": len(docs)})
    except Exception:
        _logger.exception("检索失败")
        return Fail(code=500, msg="检索失败")


@router.post("/hybrid-search", summary="混合检索（向量+关键词）")
async def hybrid_search_api(
    data: SearchInput,
    current_user: User = DependAuth,
):
    try:
        docs = await hybrid_search(
            data.query, top_k=data.top_k, collection_name=data.collection,
        )
        return Success(data={"results": docs, "count": len(docs)})
    except Exception:
        _logger.exception("混合检索失败")
        return Fail(code=500, msg="混合检索失败")


@router.post("/advanced-search", summary="高级 RAG 检索（查询改写+混合检索+重排+压缩）")
async def advanced_search_api(
    data: AdvancedSearchInput,
    current_user: User = DependAuth,
):
    try:
        config = PipelineConfig(
            enable_query_rewrite=data.enable_query_rewrite,
            enable_rerank=data.enable_rerank,
            enable_hybrid_search=data.enable_hybrid_search,
            enable_context_compress=data.enable_context_compress,
            top_k=data.top_k,
        )
        pipeline = AdvancedRAGPipeline(config)
        collection_name = data.collection if data.collection else None
        docs = await pipeline.search(
            data.query,
            collection_name=collection_name,
            doc_type=data.doc_type,
            source=data.source,
        )
        return Success(data={"results": docs, "count": len(docs)})
    except Exception:
        _logger.exception("高级检索失败")
        return Fail(code=500, msg="高级检索失败")


@router.get("/stats", summary="获取知识库统计")
async def get_stats_api(current_user: User = DependAuth):
    try:
        stats = await get_collection_stats()
        return Success(data=stats)
    except Exception:
        _logger.exception("获取统计失败")
        return Fail(code=500, msg="获取统计失败")


@router.get("/documents", summary="分页浏览文档")
async def list_documents_api(
    collection: str = Query("knowledge_base"),
    page: int = Query(1),
    page_size: int = Query(20),
    doc_type: str = Query(""),
    current_user: User = DependAuth,
):
    try:
        result = await list_documents(
            collection_name=collection,
            page=page,
            page_size=page_size,
            doc_type=doc_type,
        )
        return Success(data=result)
    except Exception:
        _logger.exception("浏览文档失败")
        return Fail(code=500, msg="浏览文档失败")


@router.get("/documents/{doc_id}/chunks", summary="获取文档分块详情")
async def get_chunks_api(
    doc_id: str,
    collection: str = Query("knowledge_base"),
    current_user: User = DependAuth,
):
    try:
        chunks = await get_document_chunks(doc_id, collection_name=collection)
        return Success(data={"chunks": chunks, "count": len(chunks)})
    except Exception:
        _logger.exception("获取分块失败")
        return Fail(code=500, msg="获取分块失败")


@router.delete("/collections/{collection}", summary="清空指定集合")
async def delete_collection_api(
    collection: str,
    current_user: User = DependAuth,
):
    if collection not in COLLECTION_NAMES:
        return Fail(code=400, msg=f"无效集合名，可选：{', '.join(COLLECTION_NAMES)}")
    try:
        await delete_all_documents(collection)
        return Success(data={"message": f"集合 [{collection}] 已清空"})
    except Exception:
        _logger.exception("清空集合失败")
        return Fail(code=500, msg="清空集合失败")


@router.post("/rebuild", summary="迁移重建：用新 embedding 模型重建所有集合")
async def rebuild_api(current_user: User = DependAuth):
    try:
        result = await rebuild_all_collections()
        return Success(data={"migrated": result})
    except Exception:
        _logger.exception("迁移重建失败")
        return Fail(code=500, msg="迁移重建失败")
