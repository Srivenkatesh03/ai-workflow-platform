from fastapi import APIRouter

from app.schemas.common import APIResponse

router = APIRouter()


@router.get("/health", response_model=APIResponse[dict[str, str]])
async def api_health() -> APIResponse[dict[str, str]]:
    return APIResponse(data={"status": "ok"})

