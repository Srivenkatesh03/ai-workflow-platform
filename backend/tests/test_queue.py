import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_db
from app.core.celery import celery_app
from app.tasks.workflow_tasks import execute_workflow_task
from app.tasks.ai_tasks import execute_ai_task
from app.services.workflow_service import WorkflowService
from app.models.execution import Execution


def test_celery_configuration():
    """Verify Celery app was correctly configured with production properties."""
    assert celery_app.main == "workflow_platform_worker"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]
    assert celery_app.conf.task_acks_late is True
    assert celery_app.conf.worker_prefetch_multiplier == 1


def test_queue_status_unauthorized():
    """Verify endpoint is JWT-protected."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/queue/status")
        assert resp.status_code == 401


def test_queue_status_authorized(monkeypatch):
    """Verify queue status endpoint returns connection details when authenticated."""
    with TestClient(app) as client:
        db_gen = get_db()
        db: Session = next(db_gen)

        # Create user
        email = f"operator-{uuid4().hex}@example.com"
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"name": "Worker Admin", "email": email, "password": "PassPassword1"},
        )
        assert reg_resp.status_code == 201
        
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "PassPassword1"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock the Redisllen and Celery control inspect active methods to prevent network calls in unit tests
        monkeypatch.setattr("redis.Redis.ping", lambda self: True)
        monkeypatch.setattr("redis.Redis.llen", lambda self, name: 5)
        monkeypatch.setattr("app.api.v1.routes.queue.get_active_workers_count", lambda: 2)

        resp = client.get("/api/v1/queue/status", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["redis_connected"] is True
        assert data["queue_length"] == 5
        assert data["active_workers"] == 2
        assert data["queue_name"] == "celery"


def test_workflow_enqueue_flow(monkeypatch):
    """Verify that execute endpoint queues execution asynchronously."""
    with TestClient(app) as client:
        db_gen = get_db()
        db: Session = next(db_gen)

        email = f"operator-{uuid4().hex}@example.com"
        client.post(
            "/api/v1/auth/register",
            json={"name": "Worker Operator", "email": email, "password": "PassPassword1"},
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "PassPassword1"},
        )
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a mock workflow
        wf_resp = client.post(
            "/api/v1/workflows",
            json={"name": "Queued Test Workflow", "steps": []},
            headers=headers
        )
        assert wf_resp.status_code == 201
        wf_id = wf_resp.json()["data"]["id"]

        # Intercept task trigger to prevent running actual task in unit tests
        task_triggered = False
        def mock_delay(*args, **kwargs):
            nonlocal task_triggered
            task_triggered = True
            return None

        monkeypatch.setattr(execute_workflow_task, "delay", mock_delay)

        # Call execute API which should now enqueue in Celery and return immediate queued state
        exec_resp = client.post(
            f"/api/v1/workflows/{wf_id}/execute",
            json={"payload": {}},
            headers=headers
        )
        assert exec_resp.status_code == 200
        assert exec_resp.json()["message"] == "Workflow execution queued"
        
        exec_data = exec_resp.json()["data"]
        assert exec_data["status"] == "queued"
        assert task_triggered is True

        # Check DB status matches 'queued'
        execution_db = db.get(Execution, UUID(exec_data["id"]))
        assert execution_db.status == "queued"
