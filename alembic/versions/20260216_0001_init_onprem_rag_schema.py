from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260216_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department",
        sa.Column("dept_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parent_dept_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["parent_dept_id"], ["department.dept_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("name", name="uq_department_name"),
    )
    op.create_index("ix_department_parent_dept_id", "department", ["parent_dept_id"], unique=False)

    op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("role_name", sa.String(length=100), nullable=False),
        sa.Column("auth_level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("role_name", name="uq_roles_role_name"),
    )

    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pwd", sa.String(length=255), nullable=False),
        sa.Column("usr_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("dept_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pwd_day", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("failure", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["dept_id"], ["department.dept_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("usr_name", name="uq_users_usr_name"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_dept_id", "users", ["dept_id"], unique=False)
    op.create_index("ix_users_role_id", "users", ["role_id"], unique=False)

    op.create_table(
        "doc_folder",
        sa.Column("folder_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("parent_folder_id", sa.Integer(), nullable=True),
        sa.Column("folder_name", sa.String(length=255), nullable=False),
        sa.Column("folder_path", sa.String(length=1024), nullable=False),
        sa.Column("dept_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["parent_folder_id"], ["doc_folder.folder_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dept_id"], ["department.dept_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("folder_path", name="uq_doc_folder_folder_path"),
    )
    op.create_index("ix_doc_folder_parent_folder_id", "doc_folder", ["parent_folder_id"], unique=False)
    op.create_index("ix_doc_folder_dept_id", "doc_folder", ["dept_id"], unique=False)

    op.create_table(
        "folder_access",
        sa.Column("access_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("folder_id", sa.Integer(), nullable=False),
        sa.Column("is_recursive", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("granted_by", sa.Integer(), nullable=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["folder_id"], ["doc_folder.folder_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.user_id"], ondelete="SET NULL"),
        sa.UniqueConstraint("user_id", "folder_id", name="uq_folder_access_user_folder"),
    )
    op.create_index("ix_folder_access_user_id", "folder_access", ["user_id"], unique=False)
    op.create_index("ix_folder_access_folder_id", "folder_access", ["folder_id"], unique=False)
    op.create_index("ix_folder_access_granted_by", "folder_access", ["granted_by"], unique=False)

    op.create_table(
        "workspace",
        sa.Column("ws_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ws_name", sa.String(length=255), nullable=False),
        sa.Column("owner_dept_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(["owner_dept_id"], ["department.dept_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_workspace_owner_dept_id", "workspace", ["owner_dept_id"], unique=False)
    op.create_index("ix_workspace_created_by", "workspace", ["created_by"], unique=False)

    op.create_table(
        "ws_permission",
        sa.Column("permission_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ws_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["ws_id"], ["workspace.ws_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("ws_id", "user_id", name="uq_ws_permission_ws_user"),
    )
    op.create_index("ix_ws_permission_ws_id", "ws_permission", ["ws_id"], unique=False)
    op.create_index("ix_ws_permission_user_id", "ws_permission", ["user_id"], unique=False)

    op.create_table(
        "ws_invitation",
        sa.Column("invite_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ws_id", sa.Integer(), nullable=False),
        sa.Column("inviter_id", sa.Integer(), nullable=False),
        sa.Column("invitee_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ws_id"], ["workspace.ws_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invitee_id"], ["users.user_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ws_invitation_ws_id", "ws_invitation", ["ws_id"], unique=False)
    op.create_index("ix_ws_invitation_inviter_id", "ws_invitation", ["inviter_id"], unique=False)
    op.create_index("ix_ws_invitation_invitee_id", "ws_invitation", ["invitee_id"], unique=False)

    op.create_table(
        "chat_session",
        sa.Column("session_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ws_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("session_type", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["ws_id"], ["workspace.ws_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_chat_session_ws_id", "chat_session", ["ws_id"], unique=False)
    op.create_index("ix_chat_session_created_by", "chat_session", ["created_by"], unique=False)

    op.create_table(
        "session_participant",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["chat_session.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("session_id", "user_id", name="uq_session_participant_session_user"),
    )
    op.create_index("ix_session_participant_session_id", "session_participant", ["session_id"], unique=False)
    op.create_index("ix_session_participant_user_id", "session_participant", ["user_id"], unique=False)

    op.create_table(
        "document",
        sa.Column("doc_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("folder_id", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(length=500), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("hash", sa.String(length=64), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("dept_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("total_page_cnt", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(length=20), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'ready'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["folder_id"], ["doc_folder.folder_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dept_id"], ["department.dept_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.role_id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("hash", name="uq_document_hash"),
    )
    op.create_index("ix_document_folder_id", "document", ["folder_id"], unique=False)
    op.create_index("ix_document_dept_id", "document", ["dept_id"], unique=False)
    op.create_index("ix_document_role_id", "document", ["role_id"], unique=False)

    op.create_table(
        "doc_chunk",
        sa.Column("chunk_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("doc_id", sa.Integer(), nullable=False),
        sa.Column("chunk_idx", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_cnt", sa.Integer(), nullable=True),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("qdrant_id", sa.String(length=200), nullable=True),
        sa.Column("embed_model", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["doc_id"], ["document.doc_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("doc_id", "chunk_idx", name="uq_doc_chunk_doc_id_chunk_idx"),
        sa.UniqueConstraint("qdrant_id", name="uq_doc_chunk_qdrant_id"),
    )
    op.create_index("ix_doc_chunk_doc_id", "doc_chunk", ["doc_id"], unique=False)

    op.create_table(
        "chat_msg",
        sa.Column("msg_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("sender_type", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["session_id"], ["chat_session.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_chat_msg_session_id", "chat_msg", ["session_id"], unique=False)
    op.create_index("ix_chat_msg_user_id", "chat_msg", ["user_id"], unique=False)

    op.create_table(
        "msg_ref",
        sa.Column("ref_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("msg_id", sa.Integer(), nullable=False),
        sa.Column("doc_id", sa.Integer(), nullable=True),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("web_url", sa.String(length=2048), nullable=True),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["msg_id"], ["chat_msg.msg_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["doc_id"], ["document.doc_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["chunk_id"], ["doc_chunk.chunk_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_msg_ref_msg_id", "msg_ref", ["msg_id"], unique=False)
    op.create_index("ix_msg_ref_doc_id", "msg_ref", ["doc_id"], unique=False)
    op.create_index("ix_msg_ref_chunk_id", "msg_ref", ["chunk_id"], unique=False)

    op.create_table(
        "access_request",
        sa.Column("req_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_ws_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("approve_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_ws_id"], ["workspace.ws_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approve_id"], ["users.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_access_request_user_id", "access_request", ["user_id"], unique=False)
    op.create_index("ix_access_request_target_ws_id", "access_request", ["target_ws_id"], unique=False)
    op.create_index("ix_access_request_approve_id", "access_request", ["approve_id"], unique=False)

    op.create_table(
        "audit_log",
        sa.Column("log_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="SET NULL"),
    )
    op.create_index("ix_audit_log_user_id", "audit_log", ["user_id"], unique=False)

    op.create_table(
        "system_job",
        sa.Column("job_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_name", sa.String(length=120), nullable=False),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'idle'")),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.UniqueConstraint("job_name", name="uq_system_job_job_name"),
    )

    op.create_table(
        "system_health",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("service_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("response_time_ms", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_system_health_service_name", "system_health", ["service_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_system_health_service_name", table_name="system_health")
    op.drop_table("system_health")

    op.drop_table("system_job")

    op.drop_index("ix_audit_log_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_access_request_approve_id", table_name="access_request")
    op.drop_index("ix_access_request_target_ws_id", table_name="access_request")
    op.drop_index("ix_access_request_user_id", table_name="access_request")
    op.drop_table("access_request")

    op.drop_index("ix_msg_ref_chunk_id", table_name="msg_ref")
    op.drop_index("ix_msg_ref_doc_id", table_name="msg_ref")
    op.drop_index("ix_msg_ref_msg_id", table_name="msg_ref")
    op.drop_table("msg_ref")

    op.drop_index("ix_chat_msg_user_id", table_name="chat_msg")
    op.drop_index("ix_chat_msg_session_id", table_name="chat_msg")
    op.drop_table("chat_msg")

    op.drop_index("ix_doc_chunk_doc_id", table_name="doc_chunk")
    op.drop_table("doc_chunk")

    op.drop_index("ix_document_role_id", table_name="document")
    op.drop_index("ix_document_dept_id", table_name="document")
    op.drop_index("ix_document_folder_id", table_name="document")
    op.drop_table("document")

    op.drop_index("ix_session_participant_user_id", table_name="session_participant")
    op.drop_index("ix_session_participant_session_id", table_name="session_participant")
    op.drop_table("session_participant")

    op.drop_index("ix_chat_session_created_by", table_name="chat_session")
    op.drop_index("ix_chat_session_ws_id", table_name="chat_session")
    op.drop_table("chat_session")

    op.drop_index("ix_ws_invitation_invitee_id", table_name="ws_invitation")
    op.drop_index("ix_ws_invitation_inviter_id", table_name="ws_invitation")
    op.drop_index("ix_ws_invitation_ws_id", table_name="ws_invitation")
    op.drop_table("ws_invitation")

    op.drop_index("ix_ws_permission_user_id", table_name="ws_permission")
    op.drop_index("ix_ws_permission_ws_id", table_name="ws_permission")
    op.drop_table("ws_permission")

    op.drop_index("ix_workspace_created_by", table_name="workspace")
    op.drop_index("ix_workspace_owner_dept_id", table_name="workspace")
    op.drop_table("workspace")

    op.drop_index("ix_folder_access_granted_by", table_name="folder_access")
    op.drop_index("ix_folder_access_folder_id", table_name="folder_access")
    op.drop_index("ix_folder_access_user_id", table_name="folder_access")
    op.drop_table("folder_access")

    op.drop_index("ix_doc_folder_dept_id", table_name="doc_folder")
    op.drop_index("ix_doc_folder_parent_folder_id", table_name="doc_folder")
    op.drop_table("doc_folder")

    op.drop_index("ix_users_role_id", table_name="users")
    op.drop_index("ix_users_dept_id", table_name="users")
    op.drop_table("users")

    op.drop_table("roles")

    op.drop_index("ix_department_parent_dept_id", table_name="department")
    op.drop_table("department")
