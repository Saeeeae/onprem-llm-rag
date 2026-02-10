"""
Hybrid Chunking Service - Standalone Text Chunking API

Methods: Semantic + Recursive Character Splitting
Port: 8003
"""
import os
from typing import List, Literal, Optional

import uvicorn
from fastapi import HTTPException
from pydantic import BaseModel, Field
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter
)

from shared.logging import setup_logging
from shared.config import BaseServiceSettings
from shared.fastapi_utils import create_service_app, add_health_endpoint, add_root_endpoint

# =============================================================================
# Configuration
# =============================================================================


class ChunkingSettings(BaseServiceSettings):
    SERVICE_NAME: str = "Hybrid Chunking"
    SERVICE_PORT: int = 8003


settings = ChunkingSettings()
logger = setup_logging(settings.SERVICE_NAME, level=settings.LOG_LEVEL)

# =============================================================================
# Request / Response Schemas
# =============================================================================


class ChunkRequest(BaseModel):
    text: str = Field(..., description="Text to chunk")
    method: Literal["recursive", "token", "hybrid"] = Field(
        "hybrid", description="Chunking method"
    )
    chunk_size: int = Field(1000, ge=100, le=4000, description="Target chunk size")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="Overlap between chunks")
    separators: Optional[List[str]] = Field(None, description="Custom separators")


class ChunkResponse(BaseModel):
    chunks: List[str]
    method: str
    chunk_count: int
    avg_chunk_length: float
    total_chars: int


# =============================================================================
# Chunking Logic
# =============================================================================


def recursive_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
) -> List[str]:
    """Recursive character text splitter respecting sentence boundaries."""
    if separators is None:
        separators = [
            "\n\n", "\n", ". ", "。", "! ", "? ", ", ", " ", ""
        ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
        is_separator_regex=False
    )
    return splitter.split_text(text)


def token_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """Token-based chunking for LLM token limits."""
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    return splitter.split_text(text)


def hybrid_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """Hybrid: Recursive splitting + semantic coherence post-processing."""
    separators = [
        "\n\n\n", "\n\n", "\n", ". ", "。", "！", "？",
        "! ", "? ", "; ", ", ", " ", ""
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len
    )
    chunks = splitter.split_text(text)

    # Merge very small chunks
    min_chunk_size = chunk_size // 4
    processed_chunks = []
    buffer = ""

    for chunk in chunks:
        if len(buffer) + len(chunk) < min_chunk_size and len(processed_chunks) > 0:
            buffer += " " + chunk
        else:
            if buffer:
                processed_chunks.append(buffer)
            buffer = chunk

    if buffer:
        processed_chunks.append(buffer)

    return processed_chunks


# =============================================================================
# FastAPI Application
# =============================================================================

app = create_service_app(
    title="Hybrid Chunking Service",
    description="Standalone text chunking service with multiple strategies",
    version="1.0.0",
)


def _health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
    }


add_health_endpoint(app, _health_check)
add_root_endpoint(app, {
    "service": settings.SERVICE_NAME,
    "methods": ["recursive", "token", "hybrid"],
    "status": "running",
})


@app.post("/chunk", response_model=ChunkResponse)
async def chunk_endpoint(request: ChunkRequest):
    """Chunk text using the specified method."""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Empty text provided")

        logger.info(
            f"Chunking {len(request.text)} chars "
            f"(method={request.method}, size={request.chunk_size}, overlap={request.chunk_overlap})"
        )

        if request.method == "recursive":
            chunks = recursive_chunking(
                request.text, request.chunk_size, request.chunk_overlap, request.separators
            )
        elif request.method == "token":
            chunks = token_chunking(
                request.text, request.chunk_size, request.chunk_overlap
            )
        elif request.method == "hybrid":
            chunks = hybrid_chunking(
                request.text, request.chunk_size, request.chunk_overlap
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")

        avg_length = sum(len(c) for c in chunks) / len(chunks) if chunks else 0

        return ChunkResponse(
            chunks=chunks,
            method=request.method,
            chunk_count=len(chunks),
            avg_chunk_length=avg_length,
            total_chars=len(request.text)
        )

    except Exception as e:
        logger.error(f"Chunking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_chunking():
    """Test endpoint with sample text."""
    try:
        test_text = """
        This is a test document with multiple paragraphs. It demonstrates how the hybrid chunking algorithm works.

        The first paragraph introduces the topic. This is important because it sets the context for the entire document.
        We want to make sure that related sentences stay together.

        The second paragraph continues the discussion. Here we add more details and examples.
        Hybrid chunking combines recursive splitting with semantic awareness.

        The third paragraph concludes the document. It summarizes the main points and provides final thoughts.
        This ensures that the document is properly segmented for retrieval.
        """

        results = {}
        for method in ["recursive", "token", "hybrid"]:
            if method == "recursive":
                chunks = recursive_chunking(test_text, chunk_size=200, chunk_overlap=50)
            elif method == "token":
                chunks = token_chunking(test_text, chunk_size=200, chunk_overlap=50)
            else:
                chunks = hybrid_chunking(test_text, chunk_size=200, chunk_overlap=50)

            results[method] = {
                "chunk_count": len(chunks),
                "chunks": chunks[:2],
                "avg_length": sum(len(c) for c in chunks) / len(chunks)
            }

        return {
            "status": "success",
            "test_text_length": len(test_text),
            "results": results
        }

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("CHUNKING_SERVICE_PORT", str(settings.SERVICE_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
