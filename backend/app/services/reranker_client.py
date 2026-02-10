"""Reranker Service Client.

Calls the BGE Reranker microservice to reorder retrieved documents
by relevance. Includes graceful fallback if the reranker is unavailable.
"""
import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

RERANKER_TIMEOUT = 60.0


async def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    reranker_url: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """Call reranker service to reorder documents by relevance.

    Args:
        query: The user's search query.
        documents: List of document dicts with at least a 'content' key.
        reranker_url: Base URL of the reranker service.
        top_k: Number of top results to return.

    Returns:
        Reranked list of document dicts with 'rerank_score' added.
        Falls back to original order (truncated to top_k) if reranker is unavailable.
    """
    if not documents:
        return documents

    try:
        doc_texts = [doc.get("content", "") for doc in documents]

        async with httpx.AsyncClient(timeout=RERANKER_TIMEOUT) as client:
            response = await client.post(
                f"{reranker_url}/rerank",
                json={
                    "query": query,
                    "documents": doc_texts,
                    "top_k": top_k,
                },
            )
            response.raise_for_status()
            result = response.json()

        # Map reranker output back to original documents
        reranked = []
        for item in result["results"]:
            idx = item["index"]
            if idx < len(documents):
                doc = documents[idx].copy()
                doc["rerank_score"] = item["relevance_score"]
                reranked.append(doc)

        logger.info(f"Reranked {len(documents)} documents, returning top {len(reranked)}")
        return reranked

    except Exception as e:
        logger.warning(f"Reranker unavailable ({e}), falling back to original order")
        return documents[:top_k]
