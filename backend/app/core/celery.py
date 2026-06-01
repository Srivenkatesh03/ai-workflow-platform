import logging
from celery import Celery
from app.core.config import settings

# Setup standard logging for the workers
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "workflow_platform_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,             # Acknowledge tasks only after successful or failed execution (prevents losing tasks on crash)
    worker_prefetch_multiplier=1,    # Prefetch 1 task at a time for fair load distribution among workers
)
