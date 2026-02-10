"""Shared test fixtures."""
import pytest
import httpx
import os

# Default service URLs for integration tests
SERVICE_URLS = {
    "backend": os.getenv("BACKEND_URL", "http://localhost:8000"),
    "ocr": os.getenv("OCR_URL", "http://localhost:8001"),
    "embedding": os.getenv("EMBEDDING_URL", "http://localhost:8002"),
    "chunking": os.getenv("CHUNKING_URL", "http://localhost:8003"),
    "reranker": os.getenv("RERANKER_URL", "http://localhost:8004"),
    "qdrant": os.getenv("QDRANT_URL", "http://localhost:6333"),
}


@pytest.fixture
def service_urls():
    """Return service URLs dict."""
    return SERVICE_URLS


@pytest.fixture
async def async_client():
    """Async HTTP client for integration tests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client
