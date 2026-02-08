"""Celery Application Configuration"""
import os
from celery import Celery
from celery.schedules import crontab

# Redis broker URL
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

# Create Celery app
app = Celery(
    "onprem_llm_worker",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=[
        "tasks.document_processing",
        "tasks.nas_sync"
    ]
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks (Celery Beat)
app.conf.beat_schedule = {
    "daily-nas-sync": {
        "task": "tasks.nas_sync.sync_nas_documents",
        "schedule": crontab(hour=2, minute=0),  # Daily at 02:00 AM
    },
    "hourly-health-check": {
        "task": "tasks.nas_sync.system_health_check",
        "schedule": crontab(minute=0),  # Every hour
    },
}


if __name__ == "__main__":
    app.start()
