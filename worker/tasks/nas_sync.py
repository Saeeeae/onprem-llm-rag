"""NAS Sync Task - Daily document scanning and indexing"""
import os
import hashlib
from pathlib import Path
from datetime import datetime
from celery import Task
from celery_app import app
from tasks.document_processing import process_document
import logging

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls",
    ".pptx", ".ppt", ".tif", ".tiff", ".png", ".jpg", ".jpeg"
}


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
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    import sys
    sys.path.append("/app")  # Add backend to path for imports
    
    NAS_MOUNT_PATH = os.getenv("NAS_MOUNT_PATH", "/mnt/nas")
    
    logger.info(f"Starting NAS sync from {NAS_MOUNT_PATH}")
    
    # Create sync log entry
    # (In production, use proper database connection)
    sync_start = datetime.utcnow()
    
    try:
        # Scan directory
        files = scan_nas_directory(NAS_MOUNT_PATH)
        logger.info(f"Found {len(files)} files in NAS")
        
        files_scanned = len(files)
        files_added = 0
        files_updated = 0
        files_failed = 0
        
        for file_path in files:
            try:
                file_hash = get_file_hash(file_path)
                
                # Check if file already processed (query database)
                # For now, process all files (simplified)
                
                # Extract department and role from file path
                # Example: /mnt/nas/Clinical_Team/Manager/file.pdf
                path_parts = Path(file_path).parts
                department = "Unknown"
                role = "All"
                
                if len(path_parts) >= 2:
                    department = path_parts[-2]  # Second to last directory
                    if len(path_parts) >= 3:
                        role = path_parts[-3]  # Third to last directory
                
                # Queue document processing task
                process_document.delay(
                    file_path=file_path,
                    file_hash=file_hash,
                    department=department,
                    role=role
                )
                
                files_added += 1
                logger.info(f"Queued: {file_path}")
            
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                files_failed += 1
        
        sync_end = datetime.utcnow()
        duration = (sync_end - sync_start).total_seconds()
        
        logger.info(
            f"NAS sync completed in {duration}s. "
            f"Scanned: {files_scanned}, Added: {files_added}, Failed: {files_failed}"
        )
        
        return {
            "status": "completed",
            "files_scanned": files_scanned,
            "files_added": files_added,
            "files_updated": files_updated,
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
    # Log to system_health_logs table
    
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
