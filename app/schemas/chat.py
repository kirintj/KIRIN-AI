from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096

class ChatResponse(BaseModel):
    message: ChatMessage
    model: str
    usage: Optional[Dict[str, Any]] = None

class ChatHistoryResponse(BaseModel):
    id: int
    username: str
    role: str
    content: str
    timestamp: str

class ChatMessageCreate(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None