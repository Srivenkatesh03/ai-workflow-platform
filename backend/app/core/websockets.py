import asyncio
import json
import logging
from uuid import UUID
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
import redis
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to client, queueing for cleanup: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_raw(self, message_str: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send raw message to client, queueing for cleanup: {e}")
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Synchronous helper to publish events to Redis (compatible with both sync Celery workers and async FastAPI)
def publish_workflow_event(event_type: str, execution_id: UUID, workflow_id: UUID, data: dict):
    try:
        r = redis.Redis.from_url(settings.redis_url)
        event_payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_id": str(execution_id),
            "workflow_id": str(workflow_id),
            "data": data
        }
        r.publish("workflow_events", json.dumps(event_payload))
    except Exception as e:
        logger.error(f"Failed to publish workflow event {event_type} to Redis: {e}")

# Helper to publish queue status updates
def publish_queue_status():
    try:
        r = redis.Redis.from_url(settings.redis_url)
        # Check queue length
        queue_len = 0
        connected = False
        try:
            r.ping()
            connected = True
            queue_len = r.llen("celery")
        except Exception:
            pass

        # Since Celery workers inspect is async / slow, we get active workers count
        # or report default based on workers connected to Redis
        active_workers = 0
        try:
            from app.core.celery import celery_app
            inspect = celery_app.control.inspect()
            active = inspect.active()
            if active:
                active_workers = len(active)
        except Exception:
            pass

        status_payload = {
            "event": "queue_updated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_id": "00000000-0000-0000-0000-000000000000",
            "workflow_id": "00000000-0000-0000-0000-000000000000",
            "data": {
                "redis_connected": connected,
                "queue_name": "celery",
                "queue_length": queue_len,
                "active_workers": active_workers,
                "error": None if connected else "Redis broker unreachable"
            }
        }
        r.publish("workflow_events", json.dumps(status_payload))
    except Exception as e:
        logger.error(f"Failed to publish queue status update to Redis: {e}")

# Background worker subscription receiver task
async def redis_pubsub_listener():
    logger.info("Initializing WebSocket Redis Pub/Sub listener background task...")
    
    while True:
        try:
            # Connect async to Redis
            r = aioredis.from_url(settings.redis_url)
            pubsub = r.pubsub()
            
            async with pubsub as ps:
                await ps.subscribe("workflow_events")
                logger.info("Successfully subscribed to Redis 'workflow_events' channel.")
                
                while True:
                    try:
                        message = await ps.get_message(ignore_subscribe_messages=True, timeout=1.0)
                        if message and message["type"] == "message":
                            data_str = message["data"].decode("utf-8")
                            await manager.broadcast_raw(data_str)
                    except ConnectionError:
                        logger.warning("Redis Pub/Sub connection lost. Attempting to reconnect...")
                        break
                    except Exception as e:
                        logger.error(f"Error in pubsub message loop: {e}")
                        await asyncio.sleep(1)
                        
        except Exception as e:
            logger.error(f"Failed to connect or subscribe to Redis Pub/Sub: {e}. Retrying in 5s...")
            await asyncio.sleep(5)
