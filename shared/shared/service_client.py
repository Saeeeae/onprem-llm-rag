"""Typed HTTP clients for inter-service communication.

Used by the worker and backend to call AI microservices.
"""
import httpx
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Client for the E5 Embedding Service."""

    def __init__(self, base_url: str = "http://embedding_service:8002", timeout: float = 180.0):
        self.base_url = base_url
        self.timeout = timeout

    async def embed(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32,
    ) -> dict:
        """Generate embeddings for a list of texts."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/embed",
                json={"texts": texts, "normalize": normalize, "batch_size": batch_size},
            )
            response.raise_for_status()
            return response.json()

    async def similarity(self, text1: str, text2: str) -> dict:
        """Calculate cosine similarity between two texts."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/similarity",
                json={"text1": text1, "text2": text2},
            )
            response.raise_for_status()
            return response.json()


class ChunkingClient:
    """Client for the Hybrid Chunking Service."""

    def __init__(self, base_url: str = "http://chunking_service:8003", timeout: float = 60.0):
        self.base_url = base_url
        self.timeout = timeout

    async def chunk(
        self,
        text: str,
        method: str = "hybrid",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> dict:
        """Chunk text using the specified method."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chunk",
                json={
                    "text": text,
                    "method": method,
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                },
            )
            response.raise_for_status()
            return response.json()


class OCRClient:
    """Client for the GLM-OCR Service."""

    def __init__(self, base_url: str = "http://ocr_service:8001", timeout: float = 120.0):
        self.base_url = base_url
        self.timeout = timeout

    async def ocr(self, file_path: str, language: str = "en") -> dict:
        """Extract text from an image file via OCR."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f)}
                data = {"language": language}
                response = await client.post(
                    f"{self.base_url}/ocr",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                return response.json()


class RerankerClient:
    """Client for the BGE Reranker Service."""

    def __init__(self, base_url: str = "http://reranker_service:8004", timeout: float = 60.0):
        self.base_url = base_url
        self.timeout = timeout

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
    ) -> dict:
        """Rerank documents by relevance to query."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {"query": query, "documents": documents}
            if top_k is not None:
                payload["top_k"] = top_k
            response = await client.post(
                f"{self.base_url}/rerank",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
