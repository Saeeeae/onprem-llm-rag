"""Audit Logging Middleware"""
import asyncio
import json
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog
from app.database import AsyncSessionLocal
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests for audit purposes"""

    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Log to database outside request path.
        if request.url.path.startswith("/api/"):
            user = getattr(request.state, "user", None)
            payload = {
                "user_id": user.user_id if user else None,
                "action_type": "api_request",
                "target_type": "endpoint",
                "description": json.dumps({
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                }),
                "ip_address": request.client.host if request.client else None,
            }
            asyncio.create_task(self._log_request(payload))

        return response

    async def _log_request(self, payload: dict):
        """Log request to database"""
        async with AsyncSessionLocal() as db:
            try:
                audit_log = AuditLog(**payload)
                db.add(audit_log)
                await db.commit()
            except Exception as e:
                logger.error(f"Error logging audit: {e}")
                await db.rollback()


async def log_chat_interaction(
    db: AsyncSession,
    user,
    query: str,
    response: str,
    retrieved_documents: list,
    token_count: int,
    latency_ms: int,
    success: bool = True,
    error_message: str = None,
    ip_address: str = None,
    user_agent: str = None
):
    """Log chat/RAG interaction to audit database"""
    try:
        description = json.dumps({
            "query": query[:500],
            "response_preview": response[:200] if response else None,
            "retrieved_doc_count": len(retrieved_documents),
            "token_count": token_count,
            "latency_ms": latency_ms,
            "success": success,
            "error": error_message,
        }, ensure_ascii=False)

        audit_log = AuditLog(
            user_id=user.user_id,
            action_type="chat_query",
            target_type="rag",
            description=description,
            ip_address=ip_address,
        )

        db.add(audit_log)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")
        await db.rollback()
