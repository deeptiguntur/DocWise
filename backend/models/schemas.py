from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UploadResponse(BaseModel):
    doc_id: str
    filename: str
    total_pages: int
    total_chunks: int
    message: str


class ChatRequest(BaseModel):
    query: str
    doc_id: str
    session_id: str
    history: Optional[List[dict]] = []


class ChatMessage(BaseModel):
    id: int
    role: str
    content: str
    tool_used: Optional[str] = None
    created_at: datetime


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]


class HealthResponse(BaseModel):
    status: str
    version: str
    app: str
