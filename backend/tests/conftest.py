import pytest
from app.core.celery import celery_app

@pytest.fixture(scope="session", autouse=True)
def configure_celery():
    celery_app.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
    )
