from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.execution import ExecutionRead
from app.schemas.workflow import ExecuteWorkflowRequest, WorkflowCreate, WorkflowRead, WorkflowUpdate
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("", response_model=APIResponse[list[WorkflowRead]])
async def list_workflows(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> APIResponse[list[WorkflowRead]]:
    return APIResponse(data=WorkflowService(db).list_workflows())


@router.post("", response_model=APIResponse[WorkflowRead], status_code=201)
async def create_workflow(
    payload: WorkflowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[WorkflowRead]:
    return APIResponse(message="Workflow created", data=WorkflowService(db).create_workflow(payload, current_user.id))


@router.get("/{workflow_id}", response_model=APIResponse[WorkflowRead])
async def get_workflow(
    workflow_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> APIResponse[WorkflowRead]:
    return APIResponse(data=WorkflowService(db).get_workflow(workflow_id))


@router.put("/{workflow_id}", response_model=APIResponse[WorkflowRead])
async def update_workflow(
    workflow_id: UUID,
    payload: WorkflowUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[WorkflowRead]:
    return APIResponse(message="Workflow updated", data=WorkflowService(db).update_workflow(workflow_id, payload))


@router.delete("/{workflow_id}", response_model=APIResponse[dict[str, str]])
async def delete_workflow(
    workflow_id: UUID, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> APIResponse[dict[str, str]]:
    WorkflowService(db).delete_workflow(workflow_id)
    return APIResponse(message="Workflow deleted", data={"id": str(workflow_id)})


@router.post("/{workflow_id}/execute", response_model=APIResponse[ExecutionRead])
async def execute_workflow(
    workflow_id: UUID,
    payload: ExecuteWorkflowRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> APIResponse[ExecutionRead]:
    return APIResponse(message="Workflow execution completed", data=WorkflowService(db).execute_workflow(workflow_id, payload))
