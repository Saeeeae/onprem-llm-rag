"""SQLAlchemy Database Models"""
from sqlalchemy import Column, String, Boolean, Integer, BigInteger, Text, ARRAY, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.sql import func
import uuid
from app.database import Base


class User(Base):
    """User model with RBAC based on Department & Role"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(String(255))
    department = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP(timezone=True))


class Document(Base):
    """Document metadata for indexed files"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(500), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(BigInteger)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)
    qdrant_point_ids = Column(ARRAY(UUID(as_uuid=True)))
    chunk_count = Column(Integer, default=0)
    indexed_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    indexed_by = Column(UUID(as_uuid=True))


class AuditLog(Base):
    """Audit log for all user actions"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True)
    username = Column(String(100))
    department = Column(String(100), index=True)
    role = Column(String(50))
    action_type = Column(String(50), nullable=False, index=True)
    query_text = Column(Text)
    response_text = Column(Text)
    retrieved_documents = Column(JSONB)
    token_count = Column(Integer)
    latency_ms = Column(Integer)
    ip_address = Column(INET)
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class SystemHealthLog(Base):
    """System health monitoring logs"""
    __tablename__ = "system_health_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    component = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    metrics = Column(JSONB)
    error_message = Column(Text)
    checked_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class DocumentProcessingQueue(Base):
    """Document processing queue for background tasks"""
    __tablename__ = "document_processing_queue"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(500), nullable=False)
    department = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='pending', index=True)
    celery_task_id = Column(String(255))
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))


class NASSyncLog(Base):
    """NAS sync operation logs"""
    __tablename__ = "nas_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sync_started_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    sync_completed_at = Column(TIMESTAMP(timezone=True))
    files_scanned = Column(Integer, default=0)
    files_added = Column(Integer, default=0)
    files_updated = Column(Integer, default=0)
    files_failed = Column(Integer, default=0)
    status = Column(String(20), default='running')
    error_message = Column(Text)
    metadata = Column(JSONB)
