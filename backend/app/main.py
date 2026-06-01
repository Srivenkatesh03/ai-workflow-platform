from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.schemas.common import APIResponse
from app.schemas.ai import AIResult


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0")
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
