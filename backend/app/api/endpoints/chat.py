"""Chat/RAG Endpoints - Handles 50 concurrent requests"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User
from app.middleware.auth import get_current_active_user
from app.middleware.logging import log_chat_interaction
from app.schemas import ChatRequest, ChatResponse, RetrievedDocument
from app.services.rag_service import rag_service
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request_body: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    RAG Chat Endpoint
    
    - Retrieves relevant documents based on user's RBAC (Department + Role)
    - Generates answer using vLLM
    - Logs interaction to audit database
    - Handles up to 50 concurrent requests with FastAPI async
    """
    try:
        # Generate RAG answer
        result = await rag_service.generate_answer(
            query=request_body.query,
            user=current_user,
            top_k=request_body.top_k or 5,
            temperature=request_body.temperature or 0.7,
            max_tokens=request_body.max_tokens or 1024
        )
        
        # Prepare response
        conversation_id = request_body.conversation_id or str(uuid4())
        
        response = ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            retrieved_documents=[
                RetrievedDocument(**doc)
                for doc in result["retrieved_documents"]
            ],
            token_count=result["token_count"],
            latency_ms=result["latency_ms"],
            model_name="vLLM"
        )
        
        # Log to audit database (async, non-blocking)
        await log_chat_interaction(
            db=db,
            user=current_user,
            query=request_body.query,
            response=result["response"],
            retrieved_documents=result["retrieved_documents"],
            token_count=result["token_count"],
            latency_ms=result["latency_ms"],
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        
        # Log error to audit
        await log_chat_interaction(
            db=db,
            user=current_user,
            query=request_body.query,
            response="",
            retrieved_documents=[],
            token_count=0,
            latency_ms=0,
            success=False,
            error_message=str(e),
            ip_address=http_request.client.host if http_request.client else None,
            user_agent=http_request.headers.get("user-agent")
        )
        
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.get("/history")
async def get_chat_history(
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chat history"""
    from sqlalchemy import select
    from app.models import AuditLog
    
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.user_id == current_user.id)
        .where(AuditLog.action_type == "query")
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "query": log.query_text,
            "response": log.response_text,
            "created_at": log.created_at.isoformat(),
            "latency_ms": log.latency_ms,
            "success": log.success
        }
        for log in logs
    ]
