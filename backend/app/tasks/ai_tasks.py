import asyncio
import logging
from app.core.celery import celery_app
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    name="app.tasks.ai_tasks.execute_ai_task"
)
def execute_ai_task(self, task_type: str, payload_dict: dict):
    """
    Asynchronous Celery worker task that executes an AI provider operation (generate or chat) in the background.
    """
    logger.info(f"Worker task execute_ai_task started: type={task_type}")
    
    db = SessionLocal()
    try:
        from app.services.ai_service import AIService
        ai_service = AIService(db)
        
        # Setup event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if task_type == "generate":
            coro = ai_service.generate(
                prompt=payload_dict["prompt"],
                provider=payload_dict.get("provider"),
                model=payload_dict.get("model"),
                timeout=payload_dict.get("timeout", 30.0),
                options=payload_dict.get("options"),
                workflow_id=payload_dict.get("workflow_id"),
                execution_id=payload_dict.get("execution_id"),
            )
        elif task_type == "chat":
            coro = ai_service.chat(
                messages=payload_dict["messages"],
                provider=payload_dict.get("provider"),
                model=payload_dict.get("model"),
                timeout=payload_dict.get("timeout", 30.0),
                options=payload_dict.get("options"),
                workflow_id=payload_dict.get("workflow_id"),
                execution_id=payload_dict.get("execution_id"),
            )
        else:
            raise ValueError(f"Unknown AI task type: {task_type}")
            
        if loop.is_running():
            import threading
            exception = None
            
            def run_in_thread():
                nonlocal exception
                try:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_loop.run_until_complete(coro)
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
            loop.run_until_complete(coro)
            
        logger.info(f"Worker task execute_ai_task completed successfully.")
    
    except Exception as exc:
        logger.warning(
            f"Worker task execute_ai_task failed on attempt {self.request.retries + 1}/{self.max_retries + 1}: {str(exc)}"
        )
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)
        try:
            self.retry(exc=exc, countdown=retry_delay)
        except Exception as retry_exc:
            logger.error("Worker task execute_ai_task retries exhausted for AI task.")
            raise retry_exc
            
    finally:
        db.close()
