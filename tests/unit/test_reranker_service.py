"""Unit tests for reranker service (model mocked)."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def reranker_app():
    """Create reranker app with mocked model."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/reranker"))

    # Mock torch before importing
    with patch.dict(os.environ, {"RERANKER_MODEL": "mock-model", "LOG_LEVEL": "DEBUG"}):
        import importlib
        import reranker_service
        importlib.reload(reranker_service)
        yield reranker_service.app


@pytest.fixture
def client(reranker_app):
    return TestClient(reranker_app)


class TestRerankerEndpoints:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_rerank_requires_query(self, client):
        response = client.post("/rerank", json={"documents": ["doc1"]})
        assert response.status_code == 422

    def test_rerank_requires_documents(self, client):
        response = client.post("/rerank", json={"query": "test"})
        assert response.status_code == 422

    def test_rerank_empty_documents(self, client):
        response = client.post("/rerank", json={"query": "test", "documents": []})
        assert response.status_code == 422
