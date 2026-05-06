import logging
from datetime import datetime

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
from app.tools.todo_tool import TodoTool
from app.tools.feedback_tool import FeedbackTool
from app.tools.conversation_tool import (
    create_conversation, list_conversations, rename_conversation,
    delete_conversation, get_messages as get_conv_messages,
    add_message as add_conv_message, get_recent_conversations,
)

router = APIRouter()
_logger = logging.getLogger(__name__)

executor = AgentExecutor(use_llm_router=False)


class AgentChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "default"
    use_llm_router: Optional[bool] = False
    use_langgraph: Optional[bool] = False
    conversation_id: Optional[str] = None


class CreateConversationRequest(BaseModel):
    title: Optional[str] = "新对话"


class RenameConversationRequest(BaseModel):
    conversation_id: str
    title: str


class ConversationIdRequest(BaseModel):
    conversation_id: str


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
            executor.use_llm_router = request.use_llm_router or False
            result = await executor.run(request.query, user_id=user_id)

        if request.conversation_id:
            add_conv_message(user_id, request.conversation_id, "user", request.query)
            add_conv_message(user_id, request.conversation_id, "assistant", result)

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


class TodoIndexRequest(BaseModel):
    index: int


class TodoUpdateRequest(BaseModel):
    index: int
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
    todos = TodoTool.get_todos_list(user_id=current_user.username)
    for i, t in enumerate(todos):
        t["_index"] = i
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
    todos = TodoTool.get_todos_list(user_id=current_user.username)
    todo_item = {
        "content": request.content,
        "priority": request.priority,
        "category": request.category,
        "due_date": request.due_date,
        "created_at": datetime.now().isoformat(),
        "done": False,
    }
    todos.append(todo_item)
    from app.tools.todo_tool import _set_user_todos
    _set_user_todos(current_user.username, todos)
    return Success(data=todo_item)


@router.put("/todos/toggle")
async def toggle_todo(
    request: TodoIndexRequest,
    current_user: User = DependAuth,
):
    success = TodoTool.toggle_todo(request.index, user_id=current_user.username)
    if success:
        return Success(data={"message": "状态已切换"})
    return Fail(code=400, msg="索引无效")


@router.put("/todos")
async def update_todo(
    request: TodoUpdateRequest,
    current_user: User = DependAuth,
):
    updates = {k: v for k, v in request.model_dump().items() if k != "index" and v is not None}
    success = TodoTool.update_todo(request.index, user_id=current_user.username, **updates)
    if success:
        return Success(data={"message": "待办已更新"})
    return Fail(code=400, msg="索引无效")


@router.delete("/todos")
async def delete_todo(
    index: int,
    current_user: User = DependAuth,
):
    success = TodoTool.delete_todo(index, user_id=current_user.username)
    if success:
        return Success(data={"message": "待办已删除"})
    return Fail(code=400, msg="索引无效")


@router.delete("/todos/completed")
async def clear_completed_todos(
    current_user: User = DependAuth,
):
    removed = TodoTool.clear_completed(user_id=current_user.username)
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
    feedback = FeedbackTool.get_feedback_list(user_id=current_user.username)
    return Success(data=feedback)


@router.get("/feedback/low-rating")
async def get_low_rating_feedback(
    threshold: int = 3,
    current_user: User = DependAuth,
):
    feedback = FeedbackTool.get_low_rating_feedback(threshold, user_id=current_user.username)
    return Success(data=feedback)


@router.get("/memory")
async def get_user_memory(
    current_user: User = DependAuth,
):
    history = get_memory(current_user.username)
    data = [{"user": u, "assistant": a} for u, a in history]
    return Success(data=data)


@router.delete("/memory")
async def clear_user_memory(
    current_user: User = DependAuth,
):
    clear_memory(current_user.username)
    return Success(data={"message": "对话记忆已清空"})


@router.get("/conversations")
async def get_conversations(
    current_user: User = DependAuth,
):
    convs = list_conversations(current_user.username)
    return Success(data=convs)


@router.post("/conversations")
async def create_new_conversation(
    request: CreateConversationRequest,
    current_user: User = DependAuth,
):
    conv = create_conversation(current_user.username, request.title or "新对话")
    return Success(data=conv)


@router.put("/conversations/rename")
async def rename_existing_conversation(
    request: RenameConversationRequest,
    current_user: User = DependAuth,
):
    success = rename_conversation(current_user.username, request.conversation_id, request.title)
    if success:
        return Success(data={"message": "重命名成功"})
    return Fail(code=404, msg="会话不存在")


@router.delete("/conversations/delete")
async def delete_existing_conversation(
    conversation_id: str,
    current_user: User = DependAuth,
):
    success = delete_conversation(current_user.username, conversation_id)
    if success:
        return Success(data={"message": "会话已删除"})
    return Fail(code=404, msg="会话不存在")


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = DependAuth,
):
    messages = get_conv_messages(current_user.username, conversation_id)
    return Success(data=messages)


@router.get("/conversations/recent")
async def get_recent(
    limit: int = 5,
    current_user: User = DependAuth,
):
    convs = get_recent_conversations(current_user.username, limit)
    return Success(data=convs)
