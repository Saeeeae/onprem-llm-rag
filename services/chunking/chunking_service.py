"""
Hybrid Chunking Service - Standalone Text Chunking API
Methods: Semantic + Recursive Character Splitting
"""
import os
import logging
from typing import List, Literal, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    TokenTextSplitter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Hybrid Chunking Service",
    description="Standalone text chunking service with multiple strategies",
    version="1.0.0"
)


class ChunkRequest(BaseModel):
    """Chunking request schema"""
    text: str = Field(..., description="Text to chunk")
    method: Literal["recursive", "token", "hybrid"] = Field(
        "hybrid",
        description="Chunking method: recursive, token, or hybrid"
    )
    chunk_size: int = Field(1000, ge=100, le=4000, description="Target chunk size")
    chunk_overlap: int = Field(200, ge=0, le=1000, description="Overlap between chunks")
    separators: Optional[List[str]] = Field(
        None,
        description="Custom separators for recursive splitting"
    )


class ChunkResponse(BaseModel):
    """Chunking response schema"""
    chunks: List[str]
    method: str
    chunk_count: int
    avg_chunk_length: float
    total_chars: int


def recursive_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
) -> List[str]:
    """
    Recursive character text splitter
    Respects sentence and paragraph boundaries
    """
    if separators is None:
        separators = [
            "\n\n",  # Paragraph
            "\n",    # Line
            ". ",    # Sentence (with space)
            "。",    # Chinese/Japanese period
            "! ",    # Exclamation
            "? ",    # Question
            ", ",    # Comma
            " ",     # Space
            ""       # Character
        ]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len,
        is_separator_regex=False
    )
    
    chunks = splitter.split_text(text)
    return chunks


def token_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Token-based chunking (useful for LLM token limits)
    """
    splitter = TokenTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    chunks = splitter.split_text(text)
    return chunks


def hybrid_chunking(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[str]:
    """
    Hybrid chunking: Recursive + Semantic awareness
    
    Strategy:
    1. First split by paragraphs/sentences (Recursive)
    2. Ensure chunks are semantically coherent
    3. Balance chunk sizes
    """
    # Step 1: Recursive splitting with semantic separators
    separators = [
        "\n\n\n",  # Multiple newlines (section break)
        "\n\n",    # Paragraph
        "\n",      # Line
        ". ",      # Sentence end
        "。",      # CJK period
        "！",      # CJK exclamation
        "？",      # CJK question
        "! ",
        "? ",
        "; ",
        ", ",
        " ",
        ""
    ]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
        length_function=len
    )
    
    chunks = splitter.split_text(text)
    
    # Step 2: Post-processing for semantic coherence
    # Merge very small chunks with adjacent chunks
    min_chunk_size = chunk_size // 4
    processed_chunks = []
    buffer = ""
    
    for chunk in chunks:
        if len(buffer) + len(chunk) < min_chunk_size and len(processed_chunks) > 0:
            # Merge with previous chunk if possible
            buffer += " " + chunk
        else:
            if buffer:
                processed_chunks.append(buffer)
            buffer = chunk
    
    if buffer:
        processed_chunks.append(buffer)
    
    return processed_chunks


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Hybrid Chunking",
        "methods": ["recursive", "token", "hybrid"],
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "chunking"
    }


@app.post("/chunk", response_model=ChunkResponse)
async def chunk_endpoint(request: ChunkRequest):
    """
    Chunking endpoint
    
    Args:
        request: ChunkRequest with text and chunking parameters
    
    Returns:
        List of text chunks
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Empty text provided")
        
        logger.info(
            f"Chunking {len(request.text)} chars "
            f"(method={request.method}, size={request.chunk_size}, overlap={request.chunk_overlap})"
        )
        
        # Select chunking method
        if request.method == "recursive":
            chunks = recursive_chunking(
                request.text,
                request.chunk_size,
                request.chunk_overlap,
                request.separators
            )
        elif request.method == "token":
            chunks = token_chunking(
                request.text,
                request.chunk_size,
                request.chunk_overlap
            )
        elif request.method == "hybrid":
            chunks = hybrid_chunking(
                request.text,
                request.chunk_size,
                request.chunk_overlap
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")
        
        # Calculate statistics
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
    """
    Test endpoint with sample text
    """
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
        
        # Test all three methods
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
                "chunks": chunks[:2],  # First 2 chunks only
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


if __name__ == "__main__":
    port = int(os.getenv("CHUNKING_SERVICE_PORT", "8003"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
