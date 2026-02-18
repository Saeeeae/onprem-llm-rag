-- =============================================================================
-- PostgreSQL Database Schema Initialization
-- On-Premise LLM & RAG System
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Users Table - RBAC based on Department & Role
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(255),
    department VARCHAR(100) NOT NULL,  -- e.g., 'Clinical_Team', 'Research', 'QA'
    role VARCHAR(50) NOT NULL,          -- e.g., 'Manager', 'Member', 'Admin'
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_department_role ON users(department, role);

-- =============================================================================
-- Documents Table - Metadata for indexed documents
-- =============================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    file_type VARCHAR(50) NOT NULL,     -- 'pdf', 'docx', 'xlsx', 'pptx', 'tif', 'png', 'jpg'
    file_size BIGINT,                   -- File size in bytes
    file_hash VARCHAR(64) UNIQUE NOT NULL,  -- SHA-256 hash for duplicate detection
    department VARCHAR(100) NOT NULL,   -- Access control: which department can access
    role VARCHAR(50) NOT NULL,          -- Access control: which role can access
    qdrant_point_ids UUID[],            -- Array of Qdrant vector IDs for this document
    chunk_count INTEGER DEFAULT 0,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    indexed_by UUID REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_documents_filename ON documents(filename);
CREATE INDEX idx_documents_file_hash ON documents(file_hash);
CREATE INDEX idx_documents_department_role ON documents(department, role);
CREATE INDEX idx_documents_indexed_at ON documents(indexed_at DESC);

-- =============================================================================
-- Audit Logs Table - Complete audit trail for compliance
-- =============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(100),              -- Denormalized for historical records
    department VARCHAR(100),            -- User's department at time of query
    role VARCHAR(50),                   -- User's role at time of query
    action_type VARCHAR(50) NOT NULL,   -- 'query', 'document_access', 'login', 'admin_action'
    query_text TEXT,                    -- User's question/prompt
    response_text TEXT,                 -- LLM's response
    retrieved_documents JSONB,          -- Array of document IDs and relevance scores
    token_count INTEGER,                -- Number of tokens used
    latency_ms INTEGER,                 -- Response time in milliseconds
    ip_address INET,                    -- User's IP address
    user_agent TEXT,                    -- Browser/client information
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    metadata JSONB,                     -- Additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_department ON audit_logs(department);

-- =============================================================================
-- System Health Logs - Monitor system performance and errors
-- =============================================================================
CREATE TABLE IF NOT EXISTS system_health_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component VARCHAR(50) NOT NULL,     -- 'vllm', 'qdrant', 'postgres', 'redis', 'celery'
    status VARCHAR(20) NOT NULL,        -- 'healthy', 'degraded', 'down'
    metrics JSONB,                      -- GPU usage, memory, queue depth, etc.
    error_message TEXT,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_health_component ON system_health_logs(component);
CREATE INDEX idx_system_health_checked_at ON system_health_logs(checked_at DESC);

-- =============================================================================
-- Document Processing Queue - Track background processing status
-- =============================================================================
CREATE TABLE IF NOT EXISTS document_processing_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    department VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    celery_task_id VARCHAR(255),       -- Celery task UUID
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_document_queue_status ON document_processing_queue(status);
CREATE INDEX idx_document_queue_created_at ON document_processing_queue(created_at DESC);

-- =============================================================================
-- NAS Sync Logs - Track daily sync operations
-- =============================================================================
CREATE TABLE IF NOT EXISTS nas_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sync_started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_completed_at TIMESTAMP WITH TIME ZONE,
    files_scanned INTEGER DEFAULT 0,
    files_added INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'
    error_message TEXT,
    metadata JSONB
);

CREATE INDEX idx_nas_sync_logs_started_at ON nas_sync_logs(sync_started_at DESC);

-- =============================================================================
-- Celery Beat Schedules (if using DatabaseScheduler)
-- =============================================================================
CREATE TABLE IF NOT EXISTS celery_periodic_tasks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    task VARCHAR(255) NOT NULL,
    crontab_schedule VARCHAR(100),      -- Cron format: '0 2 * * *'
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    total_run_count INTEGER DEFAULT 0,
    date_changed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Triggers for updated_at timestamps
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Initial Data
-- =============================================================================
-- For security, no default admin user is seeded.
-- Create the first admin manually after deployment.

-- =============================================================================
-- Views for Analytics
-- =============================================================================
CREATE OR REPLACE VIEW user_activity_summary AS
SELECT
    u.id,
    u.username,
    u.department,
    u.role,
    COUNT(al.id) AS total_queries,
    MAX(al.created_at) AS last_activity,
    AVG(al.latency_ms) AS avg_latency_ms,
    SUM(al.token_count) AS total_tokens_used
FROM users u
LEFT JOIN audit_logs al
    ON u.id = al.user_id
    AND al.action_type = 'query'
GROUP BY u.id, u.username, u.department, u.role;

CREATE OR REPLACE VIEW document_access_stats AS
SELECT
    d.id,
    d.filename,
    d.department,
    d.role,
    d.indexed_at,
    COUNT(DISTINCT al.user_id) FILTER (WHERE al.user_id IS NOT NULL) AS unique_users_accessed,
    COUNT(al.id) AS total_accesses
FROM documents d
LEFT JOIN audit_logs al
    ON al.action_type = 'query'
    AND al.retrieved_documents IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM jsonb_array_elements(al.retrieved_documents) AS doc_ref
        WHERE (doc_ref ->> 'document_id')::UUID = d.id
    )
GROUP BY d.id, d.filename, d.department, d.role, d.indexed_at;

-- =============================================================================
-- Grant Permissions
-- =============================================================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO admin;

-- =============================================================================
-- Database Ready!
-- =============================================================================
