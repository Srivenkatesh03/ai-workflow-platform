from app.core.celery import celery_app

# Autodiscover tasks from registered modules
celery_app.autodiscover_tasks(["app.tasks"])
