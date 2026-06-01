import redis
import logging
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.common import APIResponse
from app.core.celery import celery_app

router = APIRouter()
logger = logging.getLogger(__name__)


def get_redis_client():
    return redis.Redis.from_url(settings.redis_url)


def get_active_workers_count() -> int:
    try:
        inspect = celery_app.control.inspect()
        active = inspect.active()
        if active:
            return len(active)
    except Exception as exc:
        logger.warning(f"Failed to inspect active celery workers: {str(exc)}")
    return 0


@router.get("/status", response_model=APIResponse[dict])
async def get_queue_status(
    _: User = Depends(get_current_user)
) -> APIResponse[dict]:
    """
    Get current Redis connection status and queued job metrics.
    """
    client = get_redis_client()
    connected = False
    queue_len = 0
    error_msg = None
    
    try:
        client.ping()
        connected = True
        queue_len = client.llen("celery")  # Celery's default queue name is 'celery'
    except Exception as exc:
        error_msg = str(exc)
        logger.error(f"Redis queue ping failed: {error_msg}")
        
    status_data = {
        "redis_connected": connected,
        "queue_name": "celery",
        "queue_length": queue_len,
        "active_workers": get_active_workers_count(),
        "error": error_msg,
    }
    
    return APIResponse(message="Queue status retrieved", data=status_data)
