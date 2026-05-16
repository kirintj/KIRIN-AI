"""Centralized Pydantic schemas for business domain request/response models."""

from typing import Optional

from pydantic import BaseModel, Field


# ── Agent Chat ──────────────────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="用户输入")
    use_llm_router: Optional[bool] = False
    conversation_id: Optional[int] = None


# ── Conversations ───────────────────────────────────────────────────────────

class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field("新对话", max_length=200)


class RenameConversationRequest(BaseModel):
    conversation_id: int
    title: str = Field(..., min_length=1, max_length=200)


class ConversationIdRequest(BaseModel):
    conversation_id: int


# ── Todos ───────────────────────────────────────────────────────────────────

class TodoCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    priority: Optional[str] = Field("medium", pattern="^(high|medium|low)$")
    category: Optional[str] = Field("other", pattern="^(work|study|life|job|other)$")
    due_date: Optional[str] = ""


class TodoUpdateRequest(BaseModel):
    id: int
    content: Optional[str] = Field(None, max_length=500)
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    category: Optional[str] = Field(None, pattern="^(work|study|life|job|other)$")
    due_date: Optional[str] = None


class TodoIdRequest(BaseModel):
    id: int


# ── Knowledge / Documents ───────────────────────────────────────────────────

class AddDocumentRequest(BaseModel):
    documents: list[str] = Field(..., min_length=1)
    doc_ids: Optional[list[str]] = None
    collection_name: Optional[str] = "knowledge_base"
    source: Optional[str] = ""
    doc_type: Optional[str] = ""


# ── Tracker (Job Applications) ──────────────────────────────────────────────

class CreateApplicationRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    status: Optional[str] = Field("applied", pattern="^(wishlist|applied|screening|interview|offer|rejected)$")
    salary: Optional[str] = Field("", max_length=50)
    location: Optional[str] = Field("", max_length=50)
    source: Optional[str] = Field("", max_length=50)
    notes: Optional[str] = ""
    contact: Optional[str] = Field("", max_length=100)


class UpdateApplicationRequest(BaseModel):
    app_id: int
    company: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(wishlist|applied|screening|interview|offer|rejected)$")
    salary: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=50)
    source: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None
    contact: Optional[str] = Field(None, max_length=100)


class MoveApplicationRequest(BaseModel):
    app_id: int
    status: str = Field(..., pattern="^(wishlist|applied|screening|interview|offer|rejected)$")


# ── Interview Simulation ────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    company: Optional[str] = ""
    position: Optional[str] = ""
    interview_type: Optional[str] = "tech"


class InterviewChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)


class SessionIdRequest(BaseModel):
    session_id: str


# ── Job Assistant (Pipeline) ────────────────────────────────────────────────

class ResumeInput(BaseModel):
    resume_text: str = Field(..., min_length=1)


class JDInput(BaseModel):
    jd_text: str = Field(..., min_length=1)


class MatchInput(BaseModel):
    resume_json: str = Field(..., min_length=1)
    jd_json: str = Field(..., min_length=1)


class OptimizeInput(BaseModel):
    resume_text: str = Field(..., min_length=1)
    jd_text: str = Field(..., min_length=1)
    match_result: str = Field(..., min_length=1)


class PlanInput(BaseModel):
    resume_summary: str = Field(..., min_length=1)
    jd_text: str = Field(..., min_length=1)
    match_result: str = Field(..., min_length=1)


class FullPipelineInput(BaseModel):
    resume_text: str = Field(..., min_length=1)
    jd_text: str = Field(..., min_length=1)


class InterviewInput(BaseModel):
    company: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    interview_type: Optional[str] = "综合面试"


class SalaryInput(BaseModel):
    city: str = Field(..., min_length=1)
    industry: str = Field(..., min_length=1)
    position: str = Field(..., min_length=1)
    experience: Optional[str] = ""
    expected_salary: Optional[str] = "面议"


class GuideInput(BaseModel):
    scenario: str = Field(..., min_length=1)
    goal: Optional[str] = "成功求职"


class FeedbackInput(BaseModel):
    rating: int = Field(..., ge=1, le=10)
    comment: Optional[str] = ""
    related_query: Optional[str] = ""
    related_answer: Optional[str] = ""


# ── Resume Export ───────────────────────────────────────────────────────────

class GenerateResumeRequest(BaseModel):
    user_info: str = Field(..., min_length=1)
    template: Optional[str] = "classic"


class ExportDocxRequest(BaseModel):
    resume_data: dict
    template: Optional[str] = "classic"


class ExportTextRequest(BaseModel):
    resume_data: dict


# ── Chat History ────────────────────────────────────────────────────────────

class ChatHistoryUpdate(BaseModel):
    id: int
    role: Optional[str] = Field(None, pattern="^(user|assistant|system)$")
    content: Optional[str] = None
    timestamp: Optional[str] = None
