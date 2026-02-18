"""Pydantic Schemas for Request/Response validation"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# =============================================================================
# User Schemas
# =============================================================================
class UserCreate(BaseModel):
    usr_name: str
    email: str
    password: str
    dept_id: int
    role_id: int


class UserResponse(BaseModel):
    user_id: int
    usr_name: str
    email: str
    dept_id: int
    role_id: int
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =============================================================================
# Chat/RAG Schemas
# =============================================================================
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="User's question")
    conversation_id: Optional[str] = None
    stream: bool = False
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(1024, ge=1, le=4096)
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of documents to retrieve")


class RetrievedDocument(BaseModel):
    document_id: int
    filename: str
    score: float
    rerank_score: Optional[float] = None
    content: str
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    retrieved_documents: List[RetrievedDocument]
    token_count: int
    latency_ms: int
    model_name: str


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(10, ge=1, le=50)


class SearchDocument(BaseModel):
    document_id: int
    filename: str
    score: float
    content: str
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    documents: List[SearchDocument]
    total_found: int


# =============================================================================
# Document Schemas
# =============================================================================
class DocumentMetadata(BaseModel):
    doc_id: int
    file_name: str
    type: str
    size: Optional[int] = None
    dept_id: int
    role_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    dept_id: int
    role_id: int
    folder_id: Optional[int] = None
    overwrite_existing: bool = False


# =============================================================================
# Admin Schemas
# =============================================================================
class SystemHealthResponse(BaseModel):
    service_name: str
    status: str
    response_time_ms: Optional[float] = None
    metadata_json: Optional[Dict[str, Any]] = None
    checked_at: datetime


class AuditLogResponse(BaseModel):
    log_id: int
    user_id: Optional[int] = None
    action_type: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserActivityStats(BaseModel):
    total_actions: int
    unique_users: int
    top_departments: List[Dict[str, Any]]


class DocumentStats(BaseModel):
    total_documents: int
    total_chunks: int
    documents_by_type: Dict[str, int]
    documents_by_department: Dict[str, int]
    recent_uploads: List[DocumentMetadata]
