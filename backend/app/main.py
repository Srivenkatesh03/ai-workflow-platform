import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Initialize Celery app configuration early to bind shared tasks correctly
from app.worker import celery_app

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.schemas.common import APIResponse
from app.schemas.ai import AIResult


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Redis Pub/Sub receiver background listener
    from app.core.websockets import redis_pubsub_listener, publish_queue_status
    pubsub_task = asyncio.create_task(redis_pubsub_listener())
    
    # Start periodic worker activity and queue status broadcaster
    async def queue_broadcast_loop():
        await asyncio.sleep(2)  # Small startup offset
        while True:
            try:
                # Offload sync Redis/Celery checks to a separate thread
                await asyncio.to_thread(publish_queue_status)
            except Exception:
                pass
            await asyncio.sleep(8)  # Broadcast queue updates every 8 seconds

    queue_task = asyncio.create_task(queue_broadcast_loop())
    
    yield
    
    # Graceful cancellation
    pubsub_task.cancel()
    queue_task.cancel()
    try:
        await pubsub_task
        await queue_task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api/v1")

    # Expose top-level /api/generate and /api/chat directly
    from app.api.v1.routes.ai import generate as ai_generate, chat as ai_chat
    top_api_router = APIRouter(prefix="/api")
    top_api_router.post("/generate", response_model=APIResponse[AIResult])(ai_generate)
    top_api_router.post("/chat", response_model=APIResponse[AIResult])(ai_chat)
    app.include_router(top_api_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
