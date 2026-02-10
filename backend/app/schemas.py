"""Pydantic Schemas for Request/Response validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# =============================================================================
# User Schemas
# =============================================================================
class UserBase(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    department: str
    role: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
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
    document_id: UUID
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


# =============================================================================
# Document Schemas
# =============================================================================
class DocumentMetadata(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size: int
    department: str
    role: str
    chunk_count: int
    indexed_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    department: str
    role: str
    overwrite_existing: bool = False


# =============================================================================
# Admin Schemas
# =============================================================================
class SystemHealthResponse(BaseModel):
    component: str
    status: str  # 'healthy', 'degraded', 'down'
    metrics: Optional[Dict[str, Any]] = None
    last_check: datetime


class AuditLogResponse(BaseModel):
    id: UUID
    username: str
    department: str
    role: str
    action_type: str
    query_text: Optional[str]
    created_at: datetime
    success: bool
    latency_ms: Optional[int]
    
    class Config:
        from_attributes = True


class UserActivityStats(BaseModel):
    total_queries: int
    unique_users: int
    avg_latency_ms: float
    total_tokens_used: int
    top_departments: List[Dict[str, int]]


class DocumentStats(BaseModel):
    total_documents: int
    total_chunks: int
    documents_by_type: Dict[str, int]
    documents_by_department: Dict[str, int]
    recent_uploads: List[DocumentMetadata]
