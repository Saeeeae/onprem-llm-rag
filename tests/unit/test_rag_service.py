"""Unit tests for RAG service (all external services mocked)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestRAGServicePrompt:
    def test_build_rag_prompt(self):
        """Test prompt building with context documents."""
        # Import directly without needing full app context
        from app.services.rag_service import RAGService

        rag = RAGService()
        docs = [
            {"filename": "doc1.pdf", "content": "Clinical trial phase 3 results."},
            {"filename": "doc2.pdf", "content": "Patient enrollment criteria."},
        ]

        prompt = rag.build_rag_prompt("What are the trial results?", docs)

        assert "Clinical trial phase 3 results" in prompt
        assert "Patient enrollment criteria" in prompt
        assert "What are the trial results?" in prompt
        assert "Document 1: doc1.pdf" in prompt
        assert "Document 2: doc2.pdf" in prompt

    def test_build_rag_prompt_empty_docs(self):
        from app.services.rag_service import RAGService

        rag = RAGService()
        prompt = rag.build_rag_prompt("test query", [])

        assert "test query" in prompt
