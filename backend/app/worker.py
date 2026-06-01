from app.core.celery import celery_app

# Explicitly import task modules to ensure they are registered with the Celery app instance
import app.tasks.workflow_tasks
import app.tasks.ai_tasks

