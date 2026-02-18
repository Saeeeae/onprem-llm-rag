"""Admin Endpoints - System monitoring and management"""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import User, AuditLog, Document, DocChunk, SystemHealth, Department
from app.middleware.auth import get_current_admin
from app.services.qdrant_service import qdrant_service
from app.services.llm_service import vllm_service
from app.schemas import (
    SystemHealthResponse,
    UserActivityStats,
    DocumentStats,
    DocumentMetadata,
    AuditLogResponse,
)
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/health", response_model=list[SystemHealthResponse])
async def system_health(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get overall system health status"""
    health_checks = []

    # vLLM health
    vllm_healthy = await vllm_service.health_check()
    health_checks.append(SystemHealthResponse(
        service_name="vllm",
        status="healthy" if vllm_healthy else "down",
        checked_at=datetime.now(timezone.utc)
    ))

    # Qdrant health
    try:
        stats = qdrant_service.get_collection_stats()
        health_checks.append(SystemHealthResponse(
            service_name="qdrant",
            status="healthy",
            metadata_json=stats,
            checked_at=datetime.now(timezone.utc)
        ))
    except Exception:
        health_checks.append(SystemHealthResponse(
            service_name="qdrant",
            status="down",
            checked_at=datetime.now(timezone.utc)
        ))

    return health_checks


@router.get("/stats/users", response_model=UserActivityStats)
async def user_activity_stats(
    days: int = 7,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get user activity statistics"""
    since_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Total actions
    total_result = await db.execute(
        select(func.count(AuditLog.log_id))
        .where(AuditLog.created_at >= since_date)
    )
    total_actions = total_result.scalar() or 0

    # Unique users
    unique_users_result = await db.execute(
        select(func.count(func.distinct(AuditLog.user_id)))
        .where(AuditLog.created_at >= since_date)
    )
    unique_users = unique_users_result.scalar() or 0

    # Top departments (JOIN through users to department)
    top_depts_result = await db.execute(
        select(
            Department.name,
            func.count(AuditLog.log_id).label("count")
        )
        .join(User, AuditLog.user_id == User.user_id)
        .join(Department, User.dept_id == Department.dept_id)
        .where(AuditLog.created_at >= since_date)
        .group_by(Department.name)
        .order_by(func.count(AuditLog.log_id).desc())
        .limit(5)
    )
    top_departments = [
        {"department": row[0], "count": row[1]}
        for row in top_depts_result.all()
    ]

    return UserActivityStats(
        total_actions=total_actions,
        unique_users=unique_users,
        top_departments=top_departments,
    )


@router.get("/stats/documents", response_model=DocumentStats)
async def document_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get document statistics"""
    # Total documents
    total_docs_result = await db.execute(select(func.count(Document.doc_id)))
    total_documents = total_docs_result.scalar() or 0

    # Total chunks
    total_chunks_result = await db.execute(select(func.count(DocChunk.chunk_id)))
    total_chunks = total_chunks_result.scalar() or 0

    # Documents by type
    docs_by_type_result = await db.execute(
        select(
            Document.type,
            func.count(Document.doc_id).label("count")
        )
        .group_by(Document.type)
    )
    documents_by_type = {row[0]: row[1] for row in docs_by_type_result.all()}

    # Documents by department
    docs_by_dept_result = await db.execute(
        select(
            Department.name,
            func.count(Document.doc_id).label("count")
        )
        .join(Department, Document.dept_id == Department.dept_id)
        .group_by(Department.name)
    )
    documents_by_department = {row[0]: row[1] for row in docs_by_dept_result.all()}

    # Recent uploads
    recent_result = await db.execute(
        select(Document)
        .order_by(Document.created_at.desc())
        .limit(10)
    )
    recent_uploads = recent_result.scalars().all()

    return DocumentStats(
        total_documents=total_documents,
        total_chunks=total_chunks,
        documents_by_type=documents_by_type,
        documents_by_department=documents_by_department,
        recent_uploads=[DocumentMetadata.model_validate(doc) for doc in recent_uploads],
    )


@router.get("/logs/audit")
async def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_admin),
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
        AuditLogResponse.model_validate(log)
        for log in logs
    ]
