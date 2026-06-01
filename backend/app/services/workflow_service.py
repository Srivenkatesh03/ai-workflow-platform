import asyncio
import time
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.step_execution import StepExecution
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.schemas.workflow import ExecuteWorkflowRequest, WorkflowCreate, WorkflowUpdate
from app.workflows.registry import StepHandlerRegistry


class WorkflowService:
    def __init__(self, db: Session):
        self.db = db
        self.workflows = WorkflowRepository(db)
        self.executions = ExecutionRepository(db)

    def list_workflows(self):
        return self.workflows.list()

    def create_workflow(self, payload: WorkflowCreate, created_by: UUID | None = None):
        return self.workflows.create(payload, created_by)

    def get_workflow(self, workflow_id: UUID):
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow

    def update_workflow(self, workflow_id: UUID, payload: WorkflowUpdate):
        return self.workflows.update(self.get_workflow(workflow_id), payload)

    def delete_workflow(self, workflow_id: UUID) -> None:
        self.workflows.delete(self.get_workflow(workflow_id))

    def enqueue_workflow(self, workflow_id: UUID, payload: ExecuteWorkflowRequest):
        workflow = self.get_workflow(workflow_id)
        execution = self.executions.create_queued(workflow.id)
        self.executions.add_log(execution.id, f"Workflow '{workflow.name}' queued for background execution")
        import json
        self.executions.add_log(execution.id, f"INPUT_PAYLOAD: {json.dumps(payload.payload)}")
        
        # Publish 'workflow_queued' event
        from app.core.websockets import publish_workflow_event, publish_queue_status
        publish_workflow_event(
            "workflow_queued",
            execution.id,
            workflow.id,
            {
                "workflow_name": workflow.name,
                "status": "pending",
                "message": f"Workflow '{workflow.name}' queued for background execution"
            }
        )
        publish_queue_status()

        from app.tasks.workflow_tasks import execute_workflow_task
        execute_workflow_task.delay(str(workflow_id), payload.payload, str(execution.id))
        
        self.db.refresh(execution)
        return execution

    async def execute_workflow(self, workflow_id: UUID, payload: ExecuteWorkflowRequest, execution_id: UUID | None = None):
        workflow = self.get_workflow(workflow_id)
        if execution_id:
            execution = self.executions.get(execution_id)
            if not execution:
                execution = self.executions.create(workflow.id)
            else:
                execution.status = "running"
                execution.started_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(execution)
        else:
            execution = self.executions.create(workflow.id)
            
        self.executions.add_log(execution.id, f"Workflow '{workflow.name}' started")

        # Publish 'workflow_started' event
        from app.core.websockets import publish_workflow_event, publish_queue_status
        publish_workflow_event(
            "workflow_started",
            execution.id,
            workflow.id,
            {
                "workflow_name": workflow.name,
                "status": "running",
                "message": f"Workflow '{workflow.name}' started",
                "started_at": execution.started_at.isoformat() if execution.started_at else None
            }
        )
        publish_queue_status()

        # Initialize shared context for execution
        context = {
            "payload": payload.payload,
            "steps": {},
            "db": self.db,
            "execution_id": execution.id,
            "workflow_source": f"workflows/{workflow.id}",
        }


        try:
            for step in sorted(workflow.steps, key=lambda item: item.step_order):
                self.executions.add_log(execution.id, f"Executing {step.step_type} step")

                # Create running StepExecution record
                step_exec = StepExecution(
                    execution_id=execution.id,
                    step_id=step.id,
                    status="running",
                    retry_count=0,
                    duration_sec=0.0,
                    results={},
                )
                self.db.add(step_exec)
                self.db.commit()
                self.db.refresh(step_exec)

                # Publish 'step_started' event
                from app.core.websockets import publish_workflow_event
                publish_workflow_event(
                    "step_started",
                    execution.id,
                    workflow.id,
                    {
                        "step_id": str(step.id),
                        "step_order": step.step_order,
                        "step_type": step.step_type,
                        "status": "running",
                        "message": f"Executing {step.step_type} step"
                    }
                )

                handler = StepHandlerRegistry.get_handler(step.step_type)
                max_retries = step.configuration.get("max_retries", 0)
                backoff_factor = step.configuration.get("backoff_factor", 1.0)

                retry_count = 0
                success = False
                start_time = time.time()
                step_result = {}
                failure_reason = None

                while True:
                    try:
                        step_result = await handler.execute(step.configuration, context)
                        success = True
                        break
                    except Exception as step_exc:
                        failure_reason = str(step_exc)
                        self.executions.add_log(
                            execution.id,
                            f"Step {step.step_type} failed (attempt {retry_count + 1}/{max_retries + 1}): {failure_reason}",
                            "warning",
                        )
                        if retry_count < max_retries:
                            retry_count += 1
                            # Publish 'retry_triggered' event
                            publish_workflow_event(
                                "retry_triggered",
                                execution.id,
                                workflow.id,
                                {
                                    "step_id": str(step.id),
                                    "step_order": step.step_order,
                                    "step_type": step.step_type,
                                    "status": "retrying",
                                    "retry_count": retry_count,
                                    "max_retries": max_retries,
                                    "failure_reason": failure_reason,
                                    "message": f"Step {step.step_type} failed (attempt {retry_count}/{max_retries + 1}), retrying..."
                                }
                            )
                            # Exponential/linear backoff
                            delay = backoff_factor**retry_count
                            await asyncio.sleep(delay)
                        else:
                            break

                duration = time.time() - start_time
                step_exec.duration_sec = duration
                step_exec.retry_count = retry_count

                if success:
                    step_exec.status = "completed"
                    step_exec.results = step_result
                    self.db.commit()

                    # Save step result to shared context under its step type
                    context["steps"][step.step_type] = step_result
                    self.executions.add_log(execution.id, f"Step {step.step_type} completed successfully")
                    
                    # Publish 'step_completed' event
                    publish_workflow_event(
                        "step_completed",
                        execution.id,
                        workflow.id,
                        {
                            "step_id": str(step.id),
                            "step_order": step.step_order,
                            "step_type": step.step_type,
                            "status": "completed",
                            "duration_sec": duration,
                            "results": step_result,
                            "message": f"Step {step.step_type} completed successfully"
                        }
                    )
                else:
                    step_exec.status = "failed"
                    step_exec.failure_reason = failure_reason
                    self.db.commit()
                    self.executions.add_log(execution.id, f"Step {step.step_type} failed: {failure_reason}", "error")

                    # Publish 'step_failed' event
                    publish_workflow_event(
                        "step_failed",
                        execution.id,
                        workflow.id,
                        {
                            "step_id": str(step.id),
                            "step_order": step.step_order,
                            "step_type": step.step_type,
                            "status": "failed",
                            "duration_sec": duration,
                            "failure_reason": failure_reason,
                            "message": f"Step {step.step_type} failed: {failure_reason}"
                        }
                    )

                    # Check if workflow can continue despite failure
                    continue_on_error = step.configuration.get("continue_on_error", False)
                    if continue_on_error:
                        self.executions.add_log(
                            execution.id,
                            f"Continuing workflow execution despite failure of step {step.step_type} (continue_on_error=True)",
                        )
                    else:
                        raise Exception(f"Workflow execution stopped due to step {step.step_type} failure: {failure_reason}")

            if not workflow.steps:
                self.executions.add_log(execution.id, "No steps configured; execution completed")

            # Load step executions before returning to prevent lazy loading issues in async context
            self.db.refresh(execution)
            completed_execution = self.executions.complete(execution, "completed")
            
            # Publish 'workflow_completed' event
            publish_workflow_event(
                "workflow_completed",
                execution.id,
                workflow.id,
                {
                    "workflow_name": workflow.name,
                    "status": "completed",
                    "completed_at": completed_execution.completed_at.isoformat() if completed_execution.completed_at else None,
                    "message": "Workflow execution completed successfully"
                }
            )
            publish_queue_status()
            return completed_execution

        except Exception as exc:
            self.executions.add_log(execution.id, f"Workflow execution failed: {str(exc)}", "error")
            self.db.refresh(execution)
            completed_execution = self.executions.complete(execution, "failed")
            
            # Publish 'workflow_completed' event
            from app.core.websockets import publish_workflow_event, publish_queue_status
            publish_workflow_event(
                "workflow_completed",
                execution.id,
                workflow.id,
                {
                    "workflow_name": workflow.name,
                    "status": "failed",
                    "completed_at": completed_execution.completed_at.isoformat() if completed_execution.completed_at else None,
                    "message": f"Workflow execution failed: {str(exc)}"
                }
            )
            publish_queue_status()
            return completed_execution

