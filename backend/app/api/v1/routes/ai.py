from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.ai import AIResult, ClassifyRequest, SummarizeRequest, GenerateRequest, ChatRequest
from app.schemas.common import APIResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/summarize", response_model=APIResponse[AIResult])
async def summarize(
    payload: SummarizeRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[AIResult]:
    result = await AIService(db).summarize(payload.text, payload.provider)
    return APIResponse(message="Text summarized", data=result)


@router.post("/classify", response_model=APIResponse[AIResult])
async def classify(
    payload: ClassifyRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[AIResult]:
    result = await AIService(db).classify(payload.text, payload.labels, payload.provider)
    return APIResponse(message="Text classified", data=result)


@router.post("/generate", response_model=APIResponse[AIResult])
async def generate(
    payload: GenerateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[AIResult]:
    result = await AIService(db).generate(
        prompt=payload.prompt,
        provider=payload.provider,
        model=payload.model,
        timeout=payload.timeout,
        options=payload.options,
        workflow_id=payload.workflow_id,
        execution_id=payload.execution_id,
    )
    return APIResponse(message="Text generated successfully", data=result)


@router.post("/chat", response_model=APIResponse[AIResult])
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[AIResult]:
    dict_messages = [{"role": m.role, "content": m.content} for m in payload.messages]
    result = await AIService(db).chat(
        messages=dict_messages,
        provider=payload.provider,
        model=payload.model,
        timeout=payload.timeout,
        options=payload.options,
        workflow_id=payload.workflow_id,
        execution_id=payload.execution_id,
    )
    return APIResponse(message="Chat completed successfully", data=result)


@router.get("/logs", response_model=APIResponse[list[dict]])
async def get_ai_logs(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[list[dict]]:
    """
    Retrieve historical AI provider logs (Ollama, local generation, etc.)
    detailing latency, tokens, models, and execution relations.
    """
    from app.models.ai_log import AILog
    from sqlalchemy import select

    statement = select(AILog).order_by(AILog.created_at.desc()).limit(100)
    logs = db.scalars(statement).all()
    
    result_list = []
    for log in logs:
        result_list.append({
            "id": str(log.id),
            "provider": log.provider,
            "model": log.model,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "response_time_ms": log.response_time_ms,
            "workflow_id": str(log.workflow_id) if log.workflow_id else None,
            "execution_id": str(log.execution_id) if log.execution_id else None,
            "success": log.success,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
        
    return APIResponse(message="AI logs retrieved", data=result_list)



