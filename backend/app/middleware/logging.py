"""Audit Logging Middleware"""
import asyncio
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
                "user_id": user.id if user else None,
                "username": user.username if user else "anonymous",
                "department": user.department if user else None,
                "role": user.role if user else None,
                "action_type": "api_request",
                "latency_ms": latency_ms,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "success": response.status_code < 400,
                "metadata": {
                    "method": request.method,
                    "path": str(request.url.path),
                    "status_code": response.status_code,
                },
            }
            asyncio.create_task(self.log_request(payload))

        return response

    async def log_request(self, payload: dict):
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
        audit_log = AuditLog(
            user_id=user.id,
            username=user.username,
            department=user.department,
            role=user.role,
            action_type="query",
            query_text=query,
            response_text=response,
            retrieved_documents=[
                {
                    "document_id": str(doc["document_id"]),
                    "filename": doc.get("filename"),
                    "score": doc.get("score")
                }
                for doc in retrieved_documents
                if doc.get("document_id")
            ],
            token_count=token_count,
            latency_ms=latency_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        db.add(audit_log)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to log chat interaction: {e}")
        await db.rollback()
