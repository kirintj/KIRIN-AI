import logging

from fastapi import APIRouter
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.business import AgentChatRequest, AddDocumentRequest
from app.agent.executor import AgentExecutor
from app.agent.langgraph_graph import get_graph
from app.rag.chromadb_client import add_documents, delete_all_documents, get_collection_stats, list_documents, get_document_chunks
from app.services.business import conversation_service

router = APIRouter()
_logger = logging.getLogger(__name__)

executor = AgentExecutor(use_llm_router=False)


@router.post("/agent")
async def agent_chat(
    request: AgentChatRequest,
    current_user: User = DependAuth,
):
    try:
        user_id = current_user.username

        if request.use_langgraph:
            result = await _run_langgraph(request.query, user_id, request.use_llm_router)
        else:
            result = await executor.run(request.query, user_id=user_id, use_llm_router=request.use_llm_router)

        if request.conversation_id:
            await conversation_service.add_message(request.conversation_id, "user", request.query)
            await conversation_service.add_message(request.conversation_id, "assistant", result)

        return Success(data={"answer": result, "user": current_user.username})
    except Exception as e:
        _logger.exception("Agent 处理失败")
        error_msg = str(e)
        if "Arrearage" in error_msg or "Access denied" in error_msg or "overdue" in error_msg.lower():
            return Fail(code=503, msg="AI 服务暂时不可用（账户欠费），请联系管理员")
        if "rate_limit" in error_msg.lower() or "429" in error_msg:
            return Fail(code=429, msg="AI 服务繁忙，请稍后重试")
        if "timeout" in error_msg.lower():
            return Fail(code=504, msg="AI 服务响应超时，请稍后重试")
        return Fail(code=500, msg="Agent 处理失败，请稍后重试")


async def _run_langgraph(query: str, user_id: str, use_llm_router: bool) -> str:
    graph = get_graph()
    init_state = {
        "query": query,
        "user_id": user_id,
        "use_llm_router": use_llm_router or False,
        "messages": [],
        "intent": "",
        "tool_name": "",
        "tool_args": {},
        "tool_output": "",
        "iteration": 0,
        "max_iterations": 3,
        "need_more": False,
        "final_answer": "",
    }
    final_state = await graph.ainvoke(init_state)
    return final_state.get("final_answer", "抱歉，未能生成回复。")


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
