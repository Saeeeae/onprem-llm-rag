"""
BGE Reranker Service - Standalone Reranking Microservice

Model: BAAI/bge-reranker-v2-m3
Port: 8004
Role: Rerank retrieved documents by relevance score for improved RAG accuracy.
"""
import os
from typing import List, Optional

import uvicorn
from fastapi import HTTPException
from pydantic import BaseModel, Field

from shared.logging import setup_logging
from shared.device import get_device, get_torch_dtype, is_gpu_available
from shared.config import GPUServiceSettings
from shared.fastapi_utils import create_service_app, add_health_endpoint, add_root_endpoint

# =============================================================================
# Configuration
# =============================================================================


class RerankerSettings(GPUServiceSettings):
    SERVICE_NAME: str = "BGE Reranker"
    SERVICE_PORT: int = 8004
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_MODEL_PATH: str = ""
    MAX_LENGTH: int = 512


settings = RerankerSettings()
logger = setup_logging(settings.SERVICE_NAME, level=settings.LOG_LEVEL)

# =============================================================================
# Model Management (Lazy Loading)
# =============================================================================

_model = None
_tokenizer = None


def load_model():
    """Lazy load BGE reranker model and tokenizer."""
    global _model, _tokenizer
    if _model is None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        model_path = settings.RERANKER_MODEL_PATH or settings.RERANKER_MODEL
        logger.info(f"Loading reranker model from {model_path}...")

        _tokenizer = AutoTokenizer.from_pretrained(model_path)
        _model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            torch_dtype=get_torch_dtype(),
        ).to(get_device())
        _model.eval()
        logger.info(f"Reranker model loaded on {get_device()}")
    return _model, _tokenizer


# =============================================================================
# Request / Response Schemas
# =============================================================================


class RerankRequest(BaseModel):
    query: str = Field(..., description="Search query")
    documents: List[str] = Field(..., min_length=1, description="Documents to rerank")
    top_k: Optional[int] = Field(None, ge=1, description="Return top K results (default: all)")


class RerankResult(BaseModel):
    index: int
    document: str
    relevance_score: float


class RerankResponse(BaseModel):
    results: List[RerankResult]
    model: str
    query: str
    total_documents: int


# =============================================================================
# FastAPI Application
# =============================================================================

app = create_service_app(
    title="BGE Reranker Service",
    description="Reranking service using BAAI/bge-reranker-v2-m3 for improved RAG retrieval",
    version="1.0.0",
)


def _health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "model_loaded": _model is not None,
        "device": get_device(),
        "gpu_available": is_gpu_available(),
    }


add_health_endpoint(app, _health_check)
add_root_endpoint(app, {
    "service": settings.SERVICE_NAME,
    "model": settings.RERANKER_MODEL,
    "status": "running",
    "device": get_device(),
})


@app.post("/rerank", response_model=RerankResponse)
async def rerank_endpoint(request: RerankRequest):
    """Rerank documents by relevance to the query.

    Takes a query and list of document texts, returns them sorted by relevance score.
    Uses cross-encoder scoring: each (query, document) pair gets a relevance score.
    """
    import torch

    try:
        model, tokenizer = load_model()

        # Build query-document pairs for cross-encoder
        pairs = [[request.query, doc] for doc in request.documents]

        with torch.no_grad():
            inputs = tokenizer(
                pairs,
                padding=True,
                truncation=True,
                max_length=settings.MAX_LENGTH,
                return_tensors="pt",
            ).to(get_device())

            scores = model(**inputs, return_dict=True).logits.view(-1).float()

        scores_list = scores.cpu().tolist()

        # Build results sorted by score (descending)
        results = [
            RerankResult(index=i, document=doc, relevance_score=score)
            for i, (doc, score) in enumerate(zip(request.documents, scores_list))
        ]
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        # Apply top_k filter
        if request.top_k is not None:
            results = results[: request.top_k]

        return RerankResponse(
            results=results,
            model=settings.RERANKER_MODEL,
            query=request.query,
            total_documents=len(request.documents),
        )

    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_endpoint():
    """Internal test endpoint with sample data."""
    try:
        model, tokenizer = load_model()

        query = "What is the clinical trial protocol?"
        documents = [
            "The clinical trial protocol defines the study design and endpoints.",
            "Financial report for Q4 2024 shows revenue growth.",
            "Patient enrollment criteria for Phase 3 trials.",
        ]

        pairs = [[query, doc] for doc in documents]

        import torch
        with torch.no_grad():
            inputs = tokenizer(
                pairs, padding=True, truncation=True,
                max_length=settings.MAX_LENGTH, return_tensors="pt",
            ).to(get_device())
            scores = model(**inputs, return_dict=True).logits.view(-1).float()

        results = [
            {"document": doc, "score": round(score, 4)}
            for doc, score in zip(documents, scores.cpu().tolist())
        ]
        results.sort(key=lambda r: r["score"], reverse=True)

        return {
            "status": "success",
            "query": query,
            "results": results,
            "device": get_device(),
        }

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("RERANKER_SERVICE_PORT", str(settings.SERVICE_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
