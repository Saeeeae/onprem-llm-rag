"""Integration tests - end-to-end document processing pipeline."""
import pytest
import httpx


CHUNKING_URL = "http://localhost:8003"
EMBEDDING_URL = "http://localhost:8002"
RERANKER_URL = "http://localhost:8004"


@pytest.mark.integration
class TestDocumentPipeline:
    async def test_chunking_then_embedding(self):
        """Test: chunk text -> embed chunks."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Chunk
            try:
                chunk_resp = await client.post(
                    f"{CHUNKING_URL}/chunk",
                    json={
                        "text": "This is a test document for the pipeline. " * 20,
                        "method": "hybrid",
                        "chunk_size": 200,
                        "chunk_overlap": 50,
                    }
                )
            except httpx.ConnectError:
                pytest.skip("Chunking service not running")

            assert chunk_resp.status_code == 200
            chunks = chunk_resp.json()["chunks"]
            assert len(chunks) > 0

            # Step 2: Embed
            try:
                embed_resp = await client.post(
                    f"{EMBEDDING_URL}/embed",
                    json={"texts": chunks, "normalize": True}
                )
            except httpx.ConnectError:
                pytest.skip("Embedding service not running")

            assert embed_resp.status_code == 200
            embeddings = embed_resp.json()["embeddings"]
            assert len(embeddings) == len(chunks)

    async def test_reranker_pipeline(self):
        """Test: rerank documents by relevance."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                resp = await client.post(
                    f"{RERANKER_URL}/rerank",
                    json={
                        "query": "clinical trial results",
                        "documents": [
                            "The clinical trial showed positive results in phase 3.",
                            "Financial report for Q4 2024.",
                            "Patient enrollment criteria for the study.",
                        ],
                        "top_k": 2,
                    }
                )
            except httpx.ConnectError:
                pytest.skip("Reranker service not running")

            assert resp.status_code == 200
            data = resp.json()
            assert len(data["results"]) == 2
            # Most relevant document should score highest
            assert data["results"][0]["relevance_score"] >= data["results"][1]["relevance_score"]
