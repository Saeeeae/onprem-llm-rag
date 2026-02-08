"""Admin Endpoints - System monitoring and management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, AuditLog, Document, SystemHealthLog
from app.middleware.auth import get_current_superuser
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import vllm_service
from app.schemas import SystemHealthResponse, UserActivityStats, DocumentStats
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_model=list[SystemHealthResponse])
async def system_health(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get overall system health status"""
    health_checks = []
    
    # vLLM health
    vllm_healthy = await vllm_service.health_check()
    health_checks.append(SystemHealthResponse(
        component="vllm",
        status="healthy" if vllm_healthy else "down",
        last_check=datetime.utcnow()
    ))
    
    # Qdrant health
    try:
        stats = qdrant_service.get_collection_stats()
        health_checks.append(SystemHealthResponse(
            component="qdrant",
            status="healthy",
            metrics=stats,
            last_check=datetime.utcnow()
        ))
    except Exception as e:
        health_checks.append(SystemHealthResponse(
            component="qdrant",
            status="down",
            last_check=datetime.utcnow()
        ))
    
    return health_checks


@router.get("/stats/users", response_model=UserActivityStats)
async def user_activity_stats(
    days: int = 7,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get user activity statistics"""
    since_date = datetime.utcnow() - timedelta(days=days)
    
    # Total queries
    total_queries_result = await db.execute(
        select(func.count(AuditLog.id))
        .where(AuditLog.action_type == "query")
        .where(AuditLog.created_at >= since_date)
    )
    total_queries = total_queries_result.scalar()
    
    # Unique users
    unique_users_result = await db.execute(
        select(func.count(func.distinct(AuditLog.user_id)))
        .where(AuditLog.action_type == "query")
        .where(AuditLog.created_at >= since_date)
    )
    unique_users = unique_users_result.scalar()
    
    # Average latency
    avg_latency_result = await db.execute(
        select(func.avg(AuditLog.latency_ms))
        .where(AuditLog.action_type == "query")
        .where(AuditLog.created_at >= since_date)
    )
    avg_latency = avg_latency_result.scalar() or 0
    
    # Total tokens
    total_tokens_result = await db.execute(
        select(func.sum(AuditLog.token_count))
        .where(AuditLog.action_type == "query")
        .where(AuditLog.created_at >= since_date)
    )
    total_tokens = total_tokens_result.scalar() or 0
    
    # Top departments
    top_depts_result = await db.execute(
        select(
            AuditLog.department,
            func.count(AuditLog.id).label("count")
        )
        .where(AuditLog.action_type == "query")
        .where(AuditLog.created_at >= since_date)
        .group_by(AuditLog.department)
        .order_by(func.count(AuditLog.id).desc())
        .limit(5)
    )
    top_departments = [
        {"department": row[0], "count": row[1]}
        for row in top_depts_result.all()
    ]
    
    return UserActivityStats(
        total_queries=total_queries,
        unique_users=unique_users,
        avg_latency_ms=float(avg_latency),
        total_tokens_used=total_tokens,
        top_departments=top_departments
    )


@router.get("/stats/documents", response_model=DocumentStats)
async def document_stats(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get document statistics"""
    # Total documents
    total_docs_result = await db.execute(select(func.count(Document.id)))
    total_documents = total_docs_result.scalar()
    
    # Total chunks
    total_chunks_result = await db.execute(select(func.sum(Document.chunk_count)))
    total_chunks = total_chunks_result.scalar() or 0
    
    # Documents by type
    docs_by_type_result = await db.execute(
        select(
            Document.file_type,
            func.count(Document.id).label("count")
        )
        .group_by(Document.file_type)
    )
    documents_by_type = {row[0]: row[1] for row in docs_by_type_result.all()}
    
    # Documents by department
    docs_by_dept_result = await db.execute(
        select(
            Document.department,
            func.count(Document.id).label("count")
        )
        .group_by(Document.department)
    )
    documents_by_department = {row[0]: row[1] for row in docs_by_dept_result.all()}
    
    # Recent uploads
    recent_result = await db.execute(
        select(Document)
        .order_by(Document.indexed_at.desc())
        .limit(10)
    )
    recent_uploads = recent_result.scalars().all()
    
    return DocumentStats(
        total_documents=total_documents,
        total_chunks=total_chunks,
        documents_by_type=documents_by_type,
        documents_by_department=documents_by_department,
        recent_uploads=recent_uploads
    )


@router.get("/logs/audit")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs (paginated)"""
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    
    logs = result.scalars().all()
    
    return [
        {
            "id": str(log.id),
            "username": log.username,
            "department": log.department,
            "role": log.role,
            "action_type": log.action_type,
            "query_text": log.query_text[:200] if log.query_text else None,
            "created_at": log.created_at.isoformat(),
            "success": log.success,
            "latency_ms": log.latency_ms
        }
        for log in logs
    ]
