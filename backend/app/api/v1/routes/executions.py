from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.common import APIResponse
from app.schemas.execution import ExecutionRead

router = APIRouter()


@router.get("", response_model=APIResponse[list[ExecutionRead]])
async def list_executions(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> APIResponse[list[ExecutionRead]]:
    return APIResponse(data=ExecutionRepository(db).list())


@router.post("/{execution_id}/retry", response_model=APIResponse[ExecutionRead])
async def retry_execution(
    execution_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> APIResponse[ExecutionRead]:
    repository = ExecutionRepository(db)
    execution = repository.get(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    execution.status = "retrying"
    db.commit()
    db.refresh(execution)
    repository.add_log(execution.id, "Execution marked for retry")
    return APIResponse(message="Execution retry queued", data=execution)
