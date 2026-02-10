"""Integration tests - health endpoint checks for running services."""
import pytest
import httpx


SERVICES = {
    "backend": "http://localhost:8000/health",
    "ocr": "http://localhost:8001/health",
    "embedding": "http://localhost:8002/health",
    "chunking": "http://localhost:8003/health",
    "reranker": "http://localhost:8004/health",
    "qdrant": "http://localhost:6333/health",
}


@pytest.mark.integration
class TestHealthEndpoints:
    @pytest.mark.parametrize("service,url", SERVICES.items())
    async def test_service_health(self, service, url):
        """Each service should return healthy status."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(url)
                assert response.status_code == 200, f"{service} returned {response.status_code}"
                data = response.json()
                assert data.get("status") in ["healthy", "ok"], f"{service} unhealthy: {data}"
            except httpx.ConnectError:
                pytest.skip(f"{service} not running at {url}")
