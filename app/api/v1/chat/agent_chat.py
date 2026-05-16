import logging
import time

from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.business import AgentChatRequest, AddDocumentRequest
from app.agent.executor import AgentExecutor
from app.agent.rules import get_engine, reload_rules
from app.rag.chromadb_client import (
    add_documents, delete_all_documents, delete_document, move_document,
    get_collection_stats, list_documents, get_document_chunks,
    search_chromadb, search_with_filter, hybrid_search, rebuild_all_collections, COLLECTION_NAMES,
)
from app.rag.pipeline import AdvancedRAGPipeline, PipelineConfig
from app.services.business import conversation_service

router = APIRouter()
_logger = logging.getLogger(__name__)

executor = AgentExecutor(use_llm_router=False)


@router.post("/agent")
async def agent_chat(
    request: AgentChatRequest,
    current_user: User = DependAuth,
):
    start_time = time.monotonic()
    user_id = current_user.username

    try:
        result = await executor.run(request.query, user_id=user_id, use_llm_router=request.use_llm_router)

        if request.conversation_id:
            conv = await conversation_service.repo.get_by_id(request.conversation_id, user_id)
            if not conv:
                return Fail(code=403, msg="无权操作该对话")
            await conversation_service.add_message(request.conversation_id, "user", request.query)
            await conversation_service.add_message(request.conversation_id, "assistant", result)

        elapsed = time.monotonic() - start_time
        _logger.info(
            "agent_chat success",
            extra={
                "user_id": user_id,
                "query_length": len(request.query),
                "response_length": len(result),
                "elapsed_ms": round(elapsed * 1000),
                "use_llm_router": request.use_llm_router,
            },
        )
        return Success(data={"answer": result, "user": current_user.username})
    except Exception as e:
        elapsed = time.monotonic() - start_time
        error_msg = str(e)
        _logger.exception(
            "agent_chat failed",
            extra={
                "user_id": user_id,
                "error_type": type(e).__name__,
                "error_msg": error_msg[:200],
                "elapsed_ms": round(elapsed * 1000),
            },
        )
        if "Arrearage" in error_msg or "Access denied" in error_msg or "overdue" in error_msg.lower():
            return Fail(code=503, msg="AI 服务暂时不可用（账户欠费），请联系管理员")
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return Fail(code=429, msg="AI 服务繁忙，请稍后重试")
        if "timeout" in error_msg.lower():
            return Fail(code=504, msg="AI 服务响应超时，请稍后重试")
        return Fail(code=500, msg="Agent 处理失败，请稍后重试")


@router.post("/documents")
async def add_knowledge_docs(
    request: AddDocumentRequest,
    current_user: User = DependAuth,
):
    try:
        await add_documents(
            request.documents,
            request.doc_ids,
            collection_name=request.collection_name,
            source=request.source,
            doc_type=request.doc_type,
        )
        return Success(data={
            "message": "文档已添加到知识库",
            "count": len(request.documents),
            "collection": request.collection_name,
        })
    except Exception:
        _logger.exception("添加文档失败")
        return Fail(code=500, msg="添加文档失败，请稍后重试")


@router.get("/documents/stats")
async def get_knowledge_stats(
    current_user: User = DependAuth,
):
    try:
        stats = await get_collection_stats()
        return Success(data=stats)
    except Exception:
        _logger.exception("获取统计失败")
        return Fail(code=500, msg="获取统计失败，请稍后重试")


@router.delete("/documents")
async def clear_knowledge_base(
    collection_name: str = "knowledge_base",
    current_user: User = DependAuth,
):
    await delete_all_documents(collection_name)
    return Success(data={"message": f"集合 {collection_name} 已清空"})


@router.get("/documents/list")
async def list_knowledge_docs(
    collection_name: str = "knowledge_base",
    page: int = 1,
    page_size: int = 20,
    doc_type: str = "",
    current_user: User = DependAuth,
):
    try:
        result = await list_documents(
            collection_name=collection_name,
            page=page,
            page_size=page_size,
            doc_type=doc_type,
        )
        return Success(data=result)
    except Exception:
        _logger.exception("获取文档列表失败")
        return Fail(code=500, msg="获取文档列表失败")


@router.get("/documents/detail")
async def get_document_detail(
    doc_id: str,
    collection_name: str = "knowledge_base",
    current_user: User = DependAuth,
):
    try:
        chunks = await get_document_chunks(
            doc_id=doc_id,
            collection_name=collection_name,
        )
        return Success(data={"doc_id": doc_id, "chunks": chunks, "total_chunks": len(chunks)})
    except Exception:
        _logger.exception("获取文档详情失败")
        return Fail(code=500, msg="获取文档详情失败")


@router.delete("/documents/{doc_id}")
async def delete_single_document(
    doc_id: str,
    collection_name: str = "knowledge_base",
    current_user: User = DependAuth,
):
    try:
        count = await delete_document(doc_id, collection_name)
        if count == 0:
            return Fail(code=404, msg="文档不存在")
        return Success(data={"message": f"已删除文档 {doc_id}", "deleted_chunks": count})
    except Exception:
        _logger.exception("删除文档失败")
        return Fail(code=500, msg="删除文档失败")


class MoveDocumentInput(BaseModel):
    doc_id: str
    from_collection: str
    to_collection: str
    doc_type: str = ""


@router.post("/documents/move")
async def move_document_endpoint(
    data: MoveDocumentInput,
    current_user: User = DependAuth,
):
    try:
        result = await move_document(
            doc_id=data.doc_id,
            from_collection=data.from_collection,
            to_collection=data.to_collection,
            new_doc_type=data.doc_type,
        )
        if result.get("error"):
            return Fail(code=404, msg=result["error"])
        return Success(data=result)
    except Exception:
        _logger.exception("移动文档失败")
        return Fail(code=500, msg="移动文档失败")


class SearchInput(BaseModel):
    query: str
    collection_name: str = "knowledge_base"
    top_k: int = 5
    doc_type: str = ""
    source: str = ""


@router.post("/documents/search", summary="基础向量检索")
async def search_documents(
    data: SearchInput,
    current_user: User = DependAuth,
):
    try:
        if data.doc_type or data.source:
            docs = await search_with_filter(
                data.query, top_k=data.top_k,
                collection_name=data.collection_name,
                doc_type=data.doc_type, source=data.source,
            )
        else:
            docs = await search_chromadb(data.query, top_k=data.top_k, collection_name=data.collection_name)
        return Success(data={"results": docs, "count": len(docs)})
    except Exception:
        _logger.exception("检索失败")
        return Fail(code=500, msg="检索失败")


@router.post("/documents/hybrid-search", summary="混合检索（向量+关键词）")
async def hybrid_search_documents(
    data: SearchInput,
    current_user: User = DependAuth,
):
    try:
        docs = await hybrid_search(
            data.query, top_k=data.top_k, collection_name=data.collection_name,
        )
        return Success(data={"results": docs, "count": len(docs)})
    except Exception:
        _logger.exception("混合检索失败")
        return Fail(code=500, msg="混合检索失败")


class AdvancedSearchInput(BaseModel):
    query: str
    collection_name: str = ""
    top_k: int = 5
    enable_query_rewrite: bool = True
    enable_rerank: bool = True
    enable_hybrid_search: bool = True
    enable_context_compress: bool = False
    doc_type: str = ""
    source: str = ""


@router.post("/documents/advanced-search", summary="高级 RAG 检索")
async def advanced_search_documents(
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
        collection_name = data.collection_name if data.collection_name else None
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


@router.post("/documents/rebuild", summary="迁移重建：用新 embedding 模型重建所有集合")
async def rebuild_collections(current_user: User = DependAuth):
    try:
        result = await rebuild_all_collections()
        return Success(data={"migrated": result})
    except Exception:
        _logger.exception("迁移重建失败")
        return Fail(code=500, msg="迁移重建失败")


# ── 规则管理 ─────────────────────────────────────────────────────────────────


@router.get("/rules", summary="获取所有路由规则")
async def list_rules(current_user: User = DependAuth):
    engine = get_engine()
    rules = engine.get_rules()
    return Success(data={
        "rules": [
            {
                "name": r.name,
                "intent": r.intent,
                "priority": r.priority,
                "enabled": r.enabled,
                "description": r.description,
                "conditions": [
                    {
                        "type": c.type.value,
                        "values": c.values,
                        "logic": c.logic.value,
                    }
                    for c in r.conditions
                ],
            }
            for r in rules
        ],
        "total": len(rules),
    })


@router.post("/rules/reload", summary="热更新路由规则")
async def reload_rules_api(current_user: User = DependAuth):
    try:
        engine = reload_rules()
        return Success(data={
            "message": "规则已重新加载",
            "rule_count": engine.rule_count,
        })
    except Exception:
        _logger.exception("规则重载失败")
        return Fail(code=500, msg="规则重载失败")


class RuleTestInput(BaseModel):
    query: str


@router.post("/rules/test", summary="测试规则匹配")
async def test_rule(
    data: RuleTestInput,
    current_user: User = DependAuth,
):
    engine = get_engine()
    result = engine.match(data.query)
    if result:
        return Success(data={
            "matched": True,
            "intent": result.intent,
            "rule_name": result.rule_name,
        })
    return Success(data={"matched": False})
