"""SQLAlchemy Database Models - On-Premise LLM & RAG System v2"""
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, Text, Float,
    TIMESTAMP, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


# =============================================================================
# Organization & RBAC
# =============================================================================

class Department(Base):
    """Hierarchical department structure"""
    __tablename__ = "department"

    dept_id = Column(Integer, primary_key=True, autoincrement=True)
    parent_dept_id = Column(Integer, ForeignKey("department.dept_id", ondelete="SET NULL"))
    name = Column(String(100), unique=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Role(Base):
    """Role definitions with authorization levels"""
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)
    auth_level = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class User(Base):
    """User authentication & RBAC"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    pwd = Column(Text, nullable=False)
    usr_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    dept_id = Column(Integer, ForeignKey("department.dept_id", ondelete="RESTRICT"), nullable=False, index=True)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP(timezone=True))
    pwd_day = Column(Integer, default=90)
    failure = Column(Integer, default=0)
    locked_until = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True)


# =============================================================================
# Folder & Access Control
# =============================================================================

class DocFolder(Base):
    """Hierarchical folder structure for documents"""
    __tablename__ = "doc_folder"

    folder_id = Column(Integer, primary_key=True, autoincrement=True)
    parent_folder_id = Column(Integer, ForeignKey("doc_folder.folder_id", ondelete="CASCADE"))
    folder_name = Column(String(255), nullable=False)
    folder_path = Column(Text, nullable=False)
    dept_id = Column(Integer, ForeignKey("department.dept_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class FolderAccess(Base):
    """Granular folder-level access control"""
    __tablename__ = "folder_access"

    access_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    folder_id = Column(Integer, ForeignKey("doc_folder.folder_id", ondelete="CASCADE"), nullable=False)
    is_recursive = Column(Boolean, default=False)
    granted_by = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"))
    granted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True))
    is_active = Column(Boolean, default=True)


# =============================================================================
# Workspace & Collaboration
# =============================================================================

class Workspace(Base):
    """Collaboration workspace"""
    __tablename__ = "workspace"

    ws_id = Column(Integer, primary_key=True, autoincrement=True)
    ws_name = Column(String(200), nullable=False)
    owner_dept_id = Column(Integer, ForeignKey("department.dept_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class WsPermission(Base):
    """Workspace-level permissions"""
    __tablename__ = "ws_permission"

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    ws_id = Column(Integer, ForeignKey("workspace.ws_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default='viewer')


class WsInvitation(Base):
    """Workspace invitation"""
    __tablename__ = "ws_invitation"

    invite_id = Column(Integer, primary_key=True, autoincrement=True)
    ws_id = Column(Integer, ForeignKey("workspace.ws_id", ondelete="CASCADE"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    responded_at = Column(TIMESTAMP(timezone=True))


# =============================================================================
# Chat & Collaboration
# =============================================================================

class ChatSession(Base):
    """Chat session (private or shared in workspace)"""
    __tablename__ = "chat_session"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    ws_id = Column(Integer, ForeignKey("workspace.ws_id", ondelete="SET NULL"))
    created_by = Column(Integer, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True)
    title = Column(String(300))
    session_type = Column(String(20), nullable=False, default='private')
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class SessionParticipant(Base):
    """Multi-user session participation"""
    __tablename__ = "session_participant"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_session.session_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False, default='viewer')
    joined_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class ChatMsg(Base):
    """Chat message"""
    __tablename__ = "chat_msg"

    msg_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_session.session_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"))
    sender_type = Column(String(10), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class MsgRef(Base):
    """RAG source reference for a message"""
    __tablename__ = "msg_ref"

    ref_id = Column(Integer, primary_key=True, autoincrement=True)
    msg_id = Column(Integer, ForeignKey("chat_msg.msg_id", ondelete="CASCADE"), nullable=False)
    doc_id = Column(Integer, ForeignKey("document.doc_id", ondelete="SET NULL"))
    chunk_id = Column(Integer, ForeignKey("doc_chunk.chunk_id", ondelete="SET NULL"))
    web_url = Column(String(2048))
    relevance_score = Column(Float)


# =============================================================================
# Document & RAG
# =============================================================================

class Document(Base):
    """Document metadata with folder & RBAC"""
    __tablename__ = "document"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    folder_id = Column(Integer, ForeignKey("doc_folder.folder_id", ondelete="SET NULL"))
    file_name = Column(String(500), nullable=False)
    path = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)
    hash = Column(String(64), unique=True, nullable=False, index=True)
    size = Column(BigInteger)
    dept_id = Column(Integer, ForeignKey("department.dept_id", ondelete="RESTRICT"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id", ondelete="RESTRICT"), nullable=False)
    total_page_cnt = Column(Integer, default=0)
    language = Column(String(10), default='ko')
    version = Column(Integer, default=1)
    status = Column(String(20), nullable=False, default='pending', index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


class DocChunk(Base):
    """Document chunk for RAG pipeline"""
    __tablename__ = "doc_chunk"

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("document.doc_id", ondelete="CASCADE"), nullable=False)
    chunk_idx = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_cnt = Column(Integer, default=0)
    page_number = Column(Integer)
    qdrant_id = Column(String(64), index=True)
    embed_model = Column(String(100))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())


# =============================================================================
# Access Request
# =============================================================================

class AccessRequest(Base):
    """Workspace access request"""
    __tablename__ = "access_request"

    req_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    target_ws_id = Column(Integer, ForeignKey("workspace.ws_id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default='pending')
    approve_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True))


# =============================================================================
# Audit & System
# =============================================================================

class AuditLog(Base):
    """Universal activity audit log"""
    __tablename__ = "audit_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), index=True)
    action_type = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50))
    target_id = Column(Integer)
    description = Column(Text)
    ip_address = Column(String(45))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)


class SystemJob(Base):
    """Background job scheduler"""
    __tablename__ = "system_job"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(200), nullable=False)
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='idle')
    config_json = Column(JSONB)
    last_run_at = Column(TIMESTAMP(timezone=True))
    next_run_at = Column(TIMESTAMP(timezone=True))
    last_error = Column(Text)


class SystemHealth(Base):
    """Service health monitoring"""
    __tablename__ = "system_health"

    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)
    response_time_ms = Column(Float)
    metadata_json = Column(JSONB)
    checked_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
