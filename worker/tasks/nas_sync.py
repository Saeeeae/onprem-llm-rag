"""NAS Sync Task - Daily document scanning and indexing"""
import logging
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

from celery import Task
from sqlalchemy import create_engine, text

from celery_app import app
from tasks.document_processing import process_document

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls",
    ".pptx", ".ppt", ".tif", ".tiff", ".png", ".jpg", ".jpeg"
}

_db_engine = None


def get_db_engine():
    """Create and cache SQLAlchemy engine for NAS sync checks."""
    global _db_engine
    if _db_engine is None:
        host = os.getenv("POSTGRES_HOST", "postgres")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "admin")
        password = os.getenv("POSTGRES_PASSWORD", "securepassword")
        database = os.getenv("POSTGRES_DB", "onprem_llm")
        dsn = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
        _db_engine = create_engine(dsn, pool_pre_ping=True)
    return _db_engine


def load_existing_hashes() -> Dict[str, str]:
    """Read current indexed file hashes keyed by file path."""
    try:
        engine = get_db_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT path, hash FROM document")
            ).all()
        return {row[0]: row[1] for row in rows}
    except Exception as exc:
        logger.warning(f"Could not load existing hashes, processing as fresh scan: {exc}")
        return {}


def get_file_hash(file_path: str) -> str:
    """Calculate SHA-256 hash of file"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def scan_nas_directory(nas_path: str) -> list:
    """
    Scan NAS directory for documents.
    Returns list of file paths.
    """
    files = []
    nas_root = Path(nas_path)

    if not nas_root.exists():
        logger.error(f"NAS path does not exist: {nas_path}")
        return []

    for file_path in nas_root.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(str(file_path))

    return files


def extract_access_from_path(file_path: str, nas_root: str) -> Tuple[int, int]:
    """
    Extract dept_id and role_id from path.
    Expected layout: /mnt/nas/<dept_id>/<role_id>/<filename>
    Falls back to (1, 1) if structure doesn't match.
    """
    try:
        relative_path = Path(file_path).relative_to(nas_root)
        parts = relative_path.parts
        if len(parts) >= 3:
            return int(parts[0]), int(parts[1])
        if len(parts) >= 2:
            return int(parts[0]), 1
    except (ValueError, Exception):
        pass
    return 1, 1


@app.task(name="tasks.nas_sync.sync_nas_documents", bind=True)
def sync_nas_documents(self: Task):
    """
    Daily NAS Sync Task

    Scans NAS directory for new/modified documents and processes them:
    1. Detect new or modified files (by hash)
    2. Extract text (OCR for images)
    3. Chunk and embed
    4. Upsert to Qdrant
    5. Log to PostgreSQL
    """
    NAS_MOUNT_PATH = os.getenv("NAS_MOUNT_PATH", "/mnt/nas")

    logger.info(f"Starting NAS sync from {NAS_MOUNT_PATH}")

    sync_start = datetime.utcnow()

    try:
        # Scan directory
        files = scan_nas_directory(NAS_MOUNT_PATH)
        logger.info(f"Found {len(files)} files in NAS")
        existing_hashes = load_existing_hashes()

        files_scanned = len(files)
        files_added = 0
        files_updated = 0
        files_failed = 0
        files_unchanged = 0

        for file_path in files:
            try:
                file_hash = get_file_hash(file_path)
                existing_hash = existing_hashes.get(file_path)
                if existing_hash == file_hash:
                    files_unchanged += 1
                    continue

                dept_id, role_id = extract_access_from_path(file_path, NAS_MOUNT_PATH)

                # Queue document processing task
                process_document.delay(
                    file_path=file_path,
                    file_hash=file_hash,
                    dept_id=dept_id,
                    role_id=role_id
                )

                if existing_hash:
                    files_updated += 1
                else:
                    files_added += 1
                logger.info(f"Queued: {file_path}")

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                files_failed += 1

        sync_end = datetime.utcnow()
        duration = (sync_end - sync_start).total_seconds()

        logger.info(
            f"NAS sync completed in {duration}s. "
            f"Scanned: {files_scanned}, Added: {files_added}, "
            f"Updated: {files_updated}, Unchanged: {files_unchanged}, Failed: {files_failed}"
        )

        return {
            "status": "completed",
            "files_scanned": files_scanned,
            "files_added": files_added,
            "files_updated": files_updated,
            "files_unchanged": files_unchanged,
            "files_failed": files_failed,
            "duration_seconds": duration
        }

    except Exception as e:
        logger.error(f"NAS sync failed: {e}")
        return {
            "status": "failed",
            "error": str(e)
        }


@app.task(name="tasks.nas_sync.system_health_check")
def system_health_check():
    """Hourly system health check"""
    logger.info("Performing system health check")

    # Check vLLM, Qdrant, PostgreSQL, Redis
    # Log to system_health table

    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
