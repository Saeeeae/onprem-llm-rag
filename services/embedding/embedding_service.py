"""
E5 Embedding Service - Standalone Embedding API
Model: intfloat/multilingual-e5-large (1024 dimensions)
"""
import os
import logging
from typing import List, Union
import torch
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="E5 Embedding Service",
    description="Standalone embedding service using E5 multilingual model",
    version="1.0.0"
)

# Global model cache
_model = None
_device = None


def get_device():
    """Get compute device (GPU if available)"""
    global _device
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {_device}")
    return _device


def load_model():
    """Lazy load E5 embedding model"""
    global _model
    
    if _model is None:
        model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
        model_path = os.getenv("EMBEDDING_MODEL_PATH", model_name)
        
        logger.info(f"Loading E5 model from {model_path}...")
        
        try:
            _model = SentenceTransformer(
                model_path,
                device=get_device()
            )
            logger.info(f"✅ E5 model loaded successfully (dimension: {_model.get_sentence_embedding_dimension()})")
        except Exception as e:
            logger.error(f"Failed to load E5 model: {e}")
            raise
    
    return _model


class EmbedRequest(BaseModel):
    """Embedding request schema"""
    texts: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")
    normalize: bool = Field(True, description="Normalize embeddings to unit vectors")
    batch_size: int = Field(32, ge=1, le=128, description="Batch size for processing")


class EmbedResponse(BaseModel):
    """Embedding response schema"""
    embeddings: List[List[float]]
    model: str
    dimension: int
    count: int


@app.get("/")
async def root():
    """Root endpoint"""
    model = load_model()
    return {
        "service": "E5 Embedding",
        "model": os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large"),
        "dimension": model.get_sentence_embedding_dimension(),
        "status": "running",
        "device": get_device()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        device = get_device()
        model_loaded = _model is not None
        
        health_info = {
            "status": "healthy",
            "model_loaded": model_loaded,
            "device": device,
            "gpu_available": torch.cuda.is_available()
        }
        
        if model_loaded:
            health_info["dimension"] = _model.get_sentence_embedding_dimension()
        
        return health_info
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/embed", response_model=EmbedResponse)
async def embed_endpoint(request: EmbedRequest):
    """
    Embedding endpoint
    
    Args:
        request: EmbedRequest with texts to embed
    
    Returns:
        Embeddings as list of vectors
    """
    try:
        model = load_model()
        
        # Convert single text to list
        texts = [request.texts] if isinstance(request.texts, str) else request.texts
        
        if not texts:
            raise HTTPException(status_code=400, detail="No texts provided")
        
        logger.info(f"Embedding {len(texts)} texts (batch_size={request.batch_size})")
        
        # Generate embeddings
        embeddings = model.encode(
            texts,
            batch_size=request.batch_size,
            show_progress_bar=False,
            convert_to_tensor=False,
            normalize_embeddings=request.normalize
        )
        
        # Convert to list
        if isinstance(embeddings, np.ndarray):
            embeddings = embeddings.tolist()
        
        return EmbedResponse(
            embeddings=embeddings,
            model=os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large"),
            dimension=model.get_sentence_embedding_dimension(),
            count=len(embeddings)
        )
    
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similarity")
async def similarity_endpoint(text1: str, text2: str):
    """
    Calculate cosine similarity between two texts
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Cosine similarity score (0-1)
    """
    try:
        model = load_model()
        
        # Embed both texts
        embeddings = model.encode(
            [text1, text2],
            normalize_embeddings=True,
            convert_to_tensor=True
        )
        
        # Calculate cosine similarity
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
    """
    Test endpoint with sample texts
    """
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
            "sample_embedding_first_10": embeddings[0][:10].tolist() if hasattr(embeddings[0], 'tolist') else embeddings[0][:10]
        }
    
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("EMBEDDING_SERVICE_PORT", "8002"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
