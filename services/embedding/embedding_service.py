"""
E5 Embedding Service - Standalone Embedding API

Model: intfloat/multilingual-e5-large (1024 dimensions)
Port: 8002
"""
import os
from typing import List, Union

import uvicorn
import numpy as np
from sentence_transformers import SentenceTransformer
from fastapi import HTTPException
from pydantic import BaseModel, Field

from shared.logging import setup_logging
from shared.device import get_device, is_gpu_available
from shared.config import GPUServiceSettings
from shared.fastapi_utils import create_service_app, add_health_endpoint, add_root_endpoint

# =============================================================================
# Configuration
# =============================================================================


class EmbeddingSettings(GPUServiceSettings):
    SERVICE_NAME: str = "E5 Embedding"
    SERVICE_PORT: int = 8002
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-large"
    EMBEDDING_MODEL_PATH: str = ""


settings = EmbeddingSettings()
logger = setup_logging(settings.SERVICE_NAME, level=settings.LOG_LEVEL)

# =============================================================================
# Model Management (Lazy Loading)
# =============================================================================

_model = None


def load_model():
    """Lazy load E5 embedding model."""
    global _model

    if _model is None:
        model_path = settings.EMBEDDING_MODEL_PATH or settings.EMBEDDING_MODEL
        logger.info(f"Loading E5 model from {model_path}...")

        try:
            _model = SentenceTransformer(model_path, device=get_device())
            logger.info(f"E5 model loaded (dimension: {_model.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Failed to load E5 model: {e}")
            raise

    return _model


# =============================================================================
# Request / Response Schemas
# =============================================================================


class EmbedRequest(BaseModel):
    texts: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    normalize: bool = Field(True, description="Normalize embeddings to unit vectors")
    batch_size: int = Field(32, ge=1, le=128, description="Batch size for processing")


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int
    count: int


# =============================================================================
# FastAPI Application
# =============================================================================

app = create_service_app(
    title="E5 Embedding Service",
    description="Standalone embedding service using E5 multilingual model",
    version="1.0.0",
)


def _health_check():
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "model_loaded": _model is not None,
        "device": get_device(),
        "gpu_available": is_gpu_available(),
        "dimension": _model.get_sentence_embedding_dimension() if _model else None,
    }


add_health_endpoint(app, _health_check)
add_root_endpoint(app, {
    "service": settings.SERVICE_NAME,
    "model": settings.EMBEDDING_MODEL,
    "status": "running",
    "device": get_device(),
})


@app.post("/embed", response_model=EmbedResponse)
async def embed_endpoint(request: EmbedRequest):
    """Generate embeddings for provided texts."""
    try:
        model = load_model()

        texts = [request.texts] if isinstance(request.texts, str) else request.texts

        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")

        logger.info(f"Embedding {len(texts)} texts (batch_size={request.batch_size})")

        embeddings = model.encode(
            texts,
            batch_size=request.batch_size,
            show_progress_bar=False,
            convert_to_tensor=False,
            normalize_embeddings=request.normalize
        )

        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()

        return EmbedResponse(
            embeddings=embeddings,
            model=settings.EMBEDDING_MODEL,
            dimension=model.get_sentence_embedding_dimension(),
            count=len(embeddings)
        )

    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity")
async def similarity_endpoint(text1: str, text2: str):
    """Calculate cosine similarity between two texts."""
    import torch

    try:
        model = load_model()

        embeddings = model.encode(
            [text1, text2],
            normalize_embeddings=True,
            convert_to_tensor=True
        )

        similarity = torch.nn.functional.cosine_similarity(
            embeddings[0].unsqueeze(0),
            embeddings[1].unsqueeze(0)
        ).item()

        return {
            "text1": text1[:100] + "..." if len(text1) > 100 else text1,
            "text2": text2[:100] + "..." if len(text2) > 100 else text2,
            "similarity": float(similarity)
        }

    except Exception as e:
        logger.error(f"Similarity calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test")
async def test_embed():
    """Test endpoint with sample texts."""
    try:
        test_texts = [
            "This is a test sentence in English.",
            "이것은 한국어 테스트 문장입니다.",
            "これは日本語のテスト文です。",
            "这是中文测试句子。"
        ]

        model = load_model()
        embeddings = model.encode(
            test_texts,
            normalize_embeddings=True,
            convert_to_tensor=False
        )

        return {
            "status": "success",
            "test_texts": test_texts,
            "embedding_shape": embeddings.shape if hasattr(embeddings, 'shape') else (len(embeddings), len(embeddings[0])),
            "dimension": model.get_sentence_embedding_dimension(),
            "sample_embedding_first_10": embeddings[0][:10].tolist() if hasattr(embeddings[0], 'tolist') else embeddings[0][:10],
            "device": get_device(),
        }

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    port = int(os.getenv("EMBEDDING_SERVICE_PORT", str(settings.SERVICE_PORT)))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
