from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.ai import AIResult, ClassifyRequest, SummarizeRequest
from app.schemas.common import APIResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/summarize", response_model=APIResponse[AIResult])
async def summarize(payload: SummarizeRequest, _: User = Depends(get_current_user)) -> APIResponse[AIResult]:
    result = await AIService().summarize(payload.text, payload.provider)
    return APIResponse(message="Text summarized", data=result)


@router.post("/classify", response_model=APIResponse[AIResult])
async def classify(payload: ClassifyRequest, _: User = Depends(get_current_user)) -> APIResponse[AIResult]:
    result = await AIService().classify(payload.text, payload.labels, payload.provider)
    return APIResponse(message="Text classified", data=result)
