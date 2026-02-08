"""vLLM Service for LLM Inference"""
import httpx
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class vLLMService:
    """Service for communicating with vLLM inference server"""
    
    def __init__(self):
        self.base_url = settings.VLLM_URL
        self.timeout = settings.VLLM_TIMEOUT
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9,
        stop: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate completion from vLLM.
        vLLM exposes OpenAI-compatible API.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/v1/completions",
                    json={
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": top_p,
                        "stop": stop or [],
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"vLLM generation failed: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.9
    ) -> AsyncGenerator[str, None]:
        """Stream generation from vLLM"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/v1/completions",
                    json={
                        "prompt": prompt,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "top_p": top_p,
                        "stream": True,
                    }
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data != "[DONE]":
                                yield data
        except Exception as e:
            logger.error(f"vLLM streaming failed: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if vLLM service is healthy"""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False


# Singleton instance
vllm_service = vLLMService()
