"""Common Pydantic models shared across services."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class HealthResponse(BaseModel):
    """Standard health check response."""
    status: str  # "healthy" or "unhealthy"
    service: str
    model_loaded: Optional[bool] = None
    device: Optional[str] = None
    gpu_available: Optional[bool] = None
    details: Optional[Dict[str, Any]] = None


class ServiceInfoResponse(BaseModel):
    """Standard root endpoint response."""
    service: str
    version: str = "1.0.0"
    status: str = "running"
    device: Optional[str] = None
    model: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response."""
    status: str = "error"
    detail: str


class RerankRequest(BaseModel):
    """Reranker request schema."""
    query: str
    documents: List[str]
    top_k: Optional[int] = None


class RerankResult(BaseModel):
    """Single reranker result."""
    index: int
    document: str
    relevance_score: float


class RerankResponse(BaseModel):
    """Reranker response schema."""
    results: List[RerankResult]
    model: str
    query: str
