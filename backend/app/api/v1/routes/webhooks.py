from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import APIResponse
from app.schemas.workflow import ExecuteWorkflowRequest
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.post("/{workflow_id}", response_model=APIResponse[dict[str, str]])
async def receive_webhook(
    workflow_id: UUID, request: Request, db: Session = Depends(get_db)
) -> APIResponse[dict[str, str]]:
    payload = await request.json()
    execution = await WorkflowService(db).execute_workflow(workflow_id, ExecuteWorkflowRequest(payload=payload))
    return APIResponse(message="Webhook accepted", data={"execution_id": str(execution.id), "status": execution.status})
