"""FastAPI utilities: app factory, common endpoint registration.

Reduces boilerplate across service initialization.
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from typing import Optional, Callable


def create_service_app(
    title: str,
    description: str,
    version: str = "1.0.0",
    lifespan: Optional[Callable] = None,
) -> FastAPI:
    """Create a FastAPI app with standard configuration."""
    return FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
    )


def add_health_endpoint(app: FastAPI, health_checker: Callable):
    """Register a /health endpoint that calls the provided health_checker.

    The health_checker should return a dict with at minimum {"status": "healthy"}.
    If it raises, a 503 with {"status": "unhealthy"} is returned.
    """
    @app.get("/health")
    async def health_check():
        try:
            result = health_checker()
            return result
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={"status": "unhealthy", "error": str(e)},
            )


def add_root_endpoint(app: FastAPI, info: dict):
    """Register a / endpoint returning service info."""
    @app.get("/")
    async def root():
        return info
