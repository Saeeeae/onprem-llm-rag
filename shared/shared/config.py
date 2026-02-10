"""Base configuration using Pydantic Settings.

All microservices extend these base settings classes.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class BaseServiceSettings(BaseSettings):
    """Base settings shared across all microservices."""

    SERVICE_NAME: str = "unknown"
    SERVICE_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Common infrastructure
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


class GPUServiceSettings(BaseServiceSettings):
    """Extended settings for GPU-based AI services (OCR, Embedding, Reranker)."""

    CUDA_VISIBLE_DEVICES: str = "0"
    MODEL_PATH: str = ""
    MODEL_NAME: str = ""
