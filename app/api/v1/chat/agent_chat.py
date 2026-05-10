import logging

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.agent.executor import AgentExecutor
from app.agent.langgraph_graph import get_graph
from app.rag.chromadb_client import add_documents, delete_all_documents, get_collection_stats, list_documents, get_document_chunks
from app.memory.memory import get_memory, clear_memory
from app.services.business import (
    todo_service, feedback_service, conversation_service,
)

router = APIRouter()
_logger = logging.getLogger(__name__)

executor = AgentExecutor(use_llm_router=False)


class AgentChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"
    use_llm_router: Optional[bool] = False
    use_langgraph: Optional[bool] = False
    conversation_id: Optional[int] = None


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "新对话"


class RenameConversationRequest(BaseModel):
    conversation_id: int
    title: str


class ConversationIdRequest(BaseModel):
    conversation_id: int


class AddDocumentRequest(BaseModel):
    documents: list[str]
    doc_ids: Optional[list[str]] = None
    collection_name: Optional[str] = "knowledge_base"
    source: Optional[str] = ""
    doc_type: Optional[str] = ""


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
    except Exception:
        _logger.exception("Agent 处理失败")
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


class TodoIdRequest(BaseModel):
    id: int


class TodoUpdateRequest(BaseModel):
    id: int
    content: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[str] = None


class TodoCreateRequest(BaseModel):
    content: str
    priority: Optional[str] = "medium"
    category: Optional[str] = "other"
    due_date: Optional[str] = ""


@router.get("/todos")
async def list_todos(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    done: Optional[bool] = None,
    current_user: User = DependAuth,
):
    todos = await todo_service.list_todos(current_user.username)
    if category:
        todos = [t for t in todos if t.get("category") == category]
    if priority:
        todos = [t for t in todos if t.get("priority") == priority]
    if done is not None:
        todos = [t for t in todos if t.get("done") == done]
    return Success(data=todos)


@router.post("/todos")
async def create_todo(
    request: TodoCreateRequest,
    current_user: User = DependAuth,
):
    todo_item = await todo_service.create_todo(
        user_id=current_user.username,
        content=request.content,
        priority=request.priority,
        category=request.category,
        due_date=request.due_date,
    )
    return Success(data=todo_item)


@router.put("/todos/toggle")
async def toggle_todo(
    request: TodoIdRequest,
    current_user: User = DependAuth,
):
    result = await todo_service.toggle_todo(request.id, current_user.username)
    if result:
        return Success(data={"message": "状态已切换"})
    return Fail(code=400, msg="待办不存在")


@router.put("/todos")
async def update_todo(
    request: TodoUpdateRequest,
    current_user: User = DependAuth,
):
    updates = {k: v for k, v in request.model_dump().items() if k != "id" and v is not None}
    result = await todo_service.update_todo(request.id, current_user.username, **updates)
    if result:
        return Success(data={"message": "待办已更新"})
    return Fail(code=400, msg="待办不存在")


@router.delete("/todos")
async def delete_todo(
    id: int,
    current_user: User = DependAuth,
):
    success = await todo_service.delete_todo(id, current_user.username)
    if success:
        return Success(data={"message": "待办已删除"})
    return Fail(code=400, msg="待办不存在")


@router.delete("/todos/completed")
async def clear_completed_todos(
    current_user: User = DependAuth,
):
    removed = await todo_service.clear_completed(current_user.username)
    return Success(data={"message": f"已清除 {removed} 条已完成待办", "removed": removed})


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


@router.get("/feedback")
async def list_feedback(
    current_user: User = DependAuth,
):
    feedback = await feedback_service.list_feedback(current_user.username)
    return Success(data=feedback)


@router.get("/feedback/low-rating")
async def get_low_rating_feedback(
    threshold: int = 3,
    current_user: User = DependAuth,
):
    feedback = await feedback_service.get_low_rating(current_user.username, threshold)
    return Success(data=feedback)


@router.get("/memory")
async def get_user_memory(
    current_user: User = DependAuth,
):
    history = await get_memory(current_user.username)
    data = [{"user": u, "assistant": a} for u, a in history]
    return Success(data=data)


@router.delete("/memory")
async def clear_user_memory(
    current_user: User = DependAuth,
):
    await clear_memory(current_user.username)
    return Success(data={"message": "对话记忆已清空"})


@router.get("/conversations")
async def get_conversations(
    current_user: User = DependAuth,
):
    convs = await conversation_service.list_conversations(current_user.username)
    return Success(data=convs)


@router.post("/conversations")
async def create_new_conversation(
    request: CreateConversationRequest,
    current_user: User = DependAuth,
):
    conv = await conversation_service.create_conversation(current_user.username, request.title or "新对话")
    return Success(data=conv)


@router.put("/conversations/rename")
async def rename_existing_conversation(
    request: RenameConversationRequest,
    current_user: User = DependAuth,
):
    result = await conversation_service.rename_conversation(request.conversation_id, current_user.username, request.title)
    if result:
        return Success(data={"message": "重命名成功"})
    return Fail(code=404, msg="会话不存在")


@router.delete("/conversations/delete")
async def delete_existing_conversation(
    conversation_id: int,
    current_user: User = DependAuth,
):
    success = await conversation_service.delete_conversation(conversation_id, current_user.username)
    if success:
        return Success(data={"message": "会话已删除"})
    return Fail(code=404, msg="会话不存在")


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    current_user: User = DependAuth,
):
    messages = await conversation_service.get_messages_if_owner(conversation_id, current_user.username)
    if messages is None:
        return Fail(code=404, msg="会话不存在")
    return Success(data=messages)


@router.get("/conversations/recent")
async def get_recent(
    limit: int = 5,
    current_user: User = DependAuth,
):
    convs = await conversation_service.get_recent(current_user.username, limit)
    return Success(data=convs)
