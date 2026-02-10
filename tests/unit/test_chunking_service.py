"""Unit tests for chunking service logic (CPU-only, no external deps)."""
import pytest
import sys
import os

# Add service path for direct import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../services/chunking"))


class TestRecursiveChunking:
    def test_basic_chunking(self):
        from chunking_service import recursive_chunking

        text = "Hello world. " * 100
        chunks = recursive_chunking(text, chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 1
        assert all(isinstance(c, str) for c in chunks)

    def test_empty_text(self):
        from chunking_service import recursive_chunking

        chunks = recursive_chunking("", chunk_size=200, chunk_overlap=50)
        assert chunks == []

    def test_short_text_single_chunk(self):
        from chunking_service import recursive_chunking

        text = "Short text."
        chunks = recursive_chunking(text, chunk_size=200, chunk_overlap=50)
        assert len(chunks) == 1
        assert chunks[0] == text


class TestTokenChunking:
    def test_basic_chunking(self):
        from chunking_service import token_chunking

        text = "This is a test sentence. " * 50
        chunks = token_chunking(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) >= 1


class TestHybridChunking:
    def test_basic_chunking(self):
        from chunking_service import hybrid_chunking

        text = ("First paragraph with enough text to make it meaningful.\n\n"
                "Second paragraph also with sufficient content.\n\n"
                "Third paragraph concludes the test document.") * 5
        chunks = hybrid_chunking(text, chunk_size=200, chunk_overlap=50)
        assert len(chunks) >= 1

    def test_merges_small_chunks(self):
        from chunking_service import hybrid_chunking

        text = "A. B. C. D. E. F. G. H. I. J. " * 10
        chunks = hybrid_chunking(text, chunk_size=200, chunk_overlap=0)
        # After merging, no chunk should be extremely small
        for chunk in chunks:
            assert len(chunk) > 10
