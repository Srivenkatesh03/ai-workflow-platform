import asyncio
import logging
from uuid import UUID
from app.core.celery import celery_app
from app.database.session import SessionLocal
from app.services.workflow_service import WorkflowService
from app.schemas.workflow import ExecuteWorkflowRequest

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="app.tasks.workflow_tasks.execute_workflow_task"
)
def execute_workflow_task(self, workflow_id_str: str, payload_dict: dict, execution_id_str: str | None = None):
    """
    Asynchronous Celery worker task that executes a workflow's steps sequentially.
    """
    logger.info(f"Worker task execute_workflow_task started: workflow_id={workflow_id_str}, execution_id={execution_id_str}")
    
    workflow_id = UUID(workflow_id_str)
    execution_id = UUID(execution_id_str) if execution_id_str else None
    payload = ExecuteWorkflowRequest(payload=payload_dict)

    db = SessionLocal()
    try:
        service = WorkflowService(db)
        
        # Resolve or run execution in an asyncio event loop since the workflow engine is async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import threading
            exception = None
            
            def run_in_thread():
                nonlocal exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(service.execute_workflow(workflow_id, payload, execution_id))
                except Exception as e:
                    exception = e
                finally:
                    new_loop.close()
            
            thread = threading.Thread(target=run_in_thread)
            thread.start()
            thread.join()
            
            if exception:
                raise exception
        else:
            loop.run_until_complete(service.execute_workflow(workflow_id, payload, execution_id))
            
        logger.info(f"Worker task execute_workflow_task completed successfully for workflow_id={workflow_id_str}")
    
    except Exception as exc:
        logger.warning(
            f"Worker task execute_workflow_task failed on attempt {self.request.retries + 1}/{self.max_retries + 1}: {str(exc)}"
        )
        
        # Exponential backoff retry handling
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)
        
        try:
            self.retry(exc=exc, countdown=retry_delay)
        except Exception as retry_exc:
            # Retries exhausted -> Trigger Dead-Letter Foundation Routing
            logger.error(
                f"Worker task execute_workflow_task retries exhausted for execution {execution_id_str}. "
                f"Routing to Dead-Letter Failure Foundation."
            )
            
            # Record the permanent failure in the database execution logs and status
            try:
                if execution_id:
                    # Log failure in execution logs
                    service.executions.add_log(
                        execution_id,
                        f"Worker permanently failed after {self.max_retries} retries. Routing to dead-letter foundation. Last error: {str(exc)}",
                        level="error"
                    )
                    # Complete execution as failed
                    exec_record = service.executions.get(execution_id)
                    if exec_record:
                        service.executions.complete(exec_record, "failed")
            except Exception as db_exc:
                logger.critical(f"Failed to record dead-letter routing to DB for execution {execution_id_str}: {str(db_exc)}")
            
            raise retry_exc
            
    finally:
        db.close()
