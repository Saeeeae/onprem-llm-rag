# Database Schema - On-Premise LLM & RAG System v2

## Overview

PostgreSQL 16 | 18 Tables | 2 Views | Alembic Migrations

## ER Diagram

```mermaid
erDiagram
    %% ===== Organization & RBAC =====
    department {
        int dept_id PK
        int parent_dept_id FK
        varchar name UK
        timestamp created_at
    }

    roles {
        int role_id PK
        varchar role_name UK
        int auth_level
        timestamp created_at
    }

    users {
        int user_id PK
        text pwd
        varchar usr_name
        varchar email UK
        int dept_id FK
        int role_id FK
        timestamp created_at
        timestamp updated_at
        timestamp last_login
        int pwd_day
        int failure
        timestamp locked_until
        boolean is_active
    }

    %% ===== Folder Access Control =====
    doc_folder {
        int folder_id PK
        int parent_folder_id FK
        varchar folder_name
        text folder_path
        int dept_id FK
        timestamp created_at
    }

    folder_access {
        int access_id PK
        int user_id FK
        int folder_id FK
        boolean is_recursive
        int granted_by FK
        timestamp granted_at
        timestamp expires_at
        boolean is_active
    }

    %% ===== Workspace =====
    workspace {
        int ws_id PK
        varchar ws_name
        int owner_dept_id FK
        int created_by FK
        timestamp created_at
        boolean is_active
    }

    ws_permission {
        int permission_id PK
        int ws_id FK
        int user_id FK
        varchar role
    }

    ws_invitation {
        int invite_id PK
        int ws_id FK
        int inviter_id FK
        int invitee_id FK
        varchar status
        timestamp created_at
        timestamp responded_at
    }

    %% ===== Chat =====
    chat_session {
        int session_id PK
        int ws_id FK
        int created_by FK
        varchar title
        varchar session_type
        timestamp created_at
        timestamp updated_at
    }

    session_participant {
        int id PK
        int session_id FK
        int user_id FK
        varchar role
        timestamp joined_at
    }

    chat_msg {
        int msg_id PK
        int session_id FK
        int user_id FK
        varchar sender_type
        text message
        timestamp created_at
    }

    msg_ref {
        int ref_id PK
        int msg_id FK
        int doc_id FK
        int chunk_id FK
        varchar web_url
        float relevance_score
    }

    %% ===== Document & RAG =====
    document {
        int doc_id PK
        int folder_id FK
        varchar file_name
        text path
        varchar type
        varchar hash UK
        bigint size
        int dept_id FK
        int role_id FK
        int total_page_cnt
        varchar language
        int version
        varchar status
        timestamp created_at
        timestamp updated_at
    }

    doc_chunk {
        int chunk_id PK
        int doc_id FK
        int chunk_idx
        text content
        int token_cnt
        int page_number
        varchar qdrant_id
        varchar embed_model
        timestamp created_at
        timestamp updated_at
    }

    %% ===== Access Request =====
    access_request {
        int req_id PK
        int user_id FK
        int target_ws_id FK
        varchar status
        int approve_id FK
        timestamp created_at
        timestamp resolved_at
    }

    %% ===== Audit & System =====
    audit_log {
        int log_id PK
        int user_id FK
        varchar action_type
        varchar target_type
        int target_id
        text description
        varchar ip_address
        timestamp created_at
    }

    system_job {
        int job_id PK
        varchar job_name
        varchar job_type
        varchar status
        jsonb config_json
        timestamp last_run_at
        timestamp next_run_at
        text last_error
    }

    system_health {
        int id PK
        varchar service_name
        varchar status
        float response_time_ms
        jsonb metadata_json
        timestamp checked_at
    }

    %% ===== Relations =====
    department ||--o{ department : "parent"
    department ||--o{ users : "dept_id"
    department ||--o{ doc_folder : "dept_id"
    department ||--o{ workspace : "owner_dept_id"
    department ||--o{ document : "dept_id"
    roles ||--o{ users : "role_id"
    roles ||--o{ document : "role_id"

    doc_folder ||--o{ doc_folder : "parent"
    doc_folder ||--o{ document : "folder_id"
    doc_folder ||--o{ folder_access : "folder_id"
    users ||--o{ folder_access : "user_id"

    users ||--o{ workspace : "created_by"
    users ||--o{ ws_permission : "user_id"
    users ||--o{ ws_invitation : "inviter"
    users ||--o{ ws_invitation : "invitee"
    workspace ||--o{ ws_permission : "ws_id"
    workspace ||--o{ ws_invitation : "ws_id"
    workspace ||--o{ access_request : "target_ws_id"
    users ||--o{ access_request : "user_id"

    workspace ||--o{ chat_session : "ws_id"
    users ||--o{ chat_session : "created_by"
    chat_session ||--o{ session_participant : "session_id"
    users ||--o{ session_participant : "user_id"
    chat_session ||--o{ chat_msg : "session_id"
    users ||--o{ chat_msg : "user_id"
    chat_msg ||--o{ msg_ref : "msg_id"
    document ||--o{ msg_ref : "doc_id"
    doc_chunk ||--o{ msg_ref : "chunk_id"
    document ||--o{ doc_chunk : "doc_id"

    users ||--o{ audit_log : "user_id"
```

## Table Groups

### Organization & RBAC (3 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `department` | Hierarchical dept structure | `parent_dept_id` for tree |
| `roles` | Role definitions | `auth_level` for access hierarchy |
| `users` | Authentication & profile | FK to dept + role, `locked_until` for security |

### Folder Access Control (2 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `doc_folder` | Hierarchical folder structure | `parent_folder_id`, `folder_path` |
| `folder_access` | Per-user folder permissions | `is_recursive`, `expires_at` for temporal access |

### Workspace & Collaboration (3 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `workspace` | Collaboration spaces | `owner_dept_id`, `is_active` |
| `ws_permission` | User roles in workspace | `role`: owner/editor/viewer |
| `ws_invitation` | Workspace invitations | `status`: pending/accepted/rejected |

### Chat (4 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `chat_session` | Chat conversations | `session_type`: private/shared |
| `session_participant` | Multi-user sessions | `role`: owner/editor/viewer |
| `chat_msg` | Individual messages | `sender_type`: user/assistant/system |
| `msg_ref` | RAG source references | `doc_id`, `chunk_id`, `relevance_score` |

### Document & RAG (2 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `document` | File metadata + RBAC | `status`: pending/processing/indexed/failed |
| `doc_chunk` | Chunks for vector search | `qdrant_id`, `embed_model`, `token_cnt` |

### System (4 tables)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `access_request` | Workspace access requests | `status`: pending/approved/rejected |
| `audit_log` | Universal activity tracking | `action_type`, `target_type` + `target_id` |
| `system_job` | Background job scheduler | `config_json` (JSONB), `next_run_at` |
| `system_health` | Service health monitoring | `service_name`, `response_time_ms` |

## Access Control Flow

```
User Request
    |
    v
[1] Check users.is_active & locked_until
    |
    v
[2] Resolve dept_id -> department (+ parent hierarchy)
    |
    v
[3] Resolve role_id -> roles.auth_level
    |
    v
[4] Check folder_access (user_id + folder_id, is_recursive, expires_at)
    |
    v
[5] Check ws_permission (if workspace-scoped request)
    |
    v
[6] Filter documents by dept_id + role_id + folder access
    |
    v
[7] Log to audit_log
```

## Views

| View | Purpose |
|------|---------|
| `user_activity_summary` | Per-user action counts, query counts, last activity |
| `document_stats` | Per-document chunk counts, department, folder, status |

## Seed Data

Initial deployment creates:
- **Departments**: Admin, Research, Clinical_Team, QA
- **Roles**: Admin (100), Manager (50), Member (10), Viewer (1)

## Schema Files

| File | Purpose |
|------|---------|
| `database/init.sql` | Full DDL for fresh PostgreSQL setup |
| `backend/app/models.py` | SQLAlchemy ORM models |
| `alembic/versions/20260216_0001_*.py` | Alembic migration (v1) |
