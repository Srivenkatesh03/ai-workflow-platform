import asyncio
import time
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.workflows.registry import StepHandlerRegistry


def test_workflow_end_to_end():
    email = f"user-{uuid4().hex}@example.com"
    password = "StrongPass123"

    with TestClient(app) as client:
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"name": "Engine Tester", "email": email, "password": password},
        )
        login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a workflow with steps
        workflow_data = {
            "name": "E2E AI Workflow",
            "description": "Tests all step handlers in sequence",
            "trigger_type": "manual",
            "steps": [
                {
                    "step_order": 1,
                    "step_type": "ai_summarize",
                    "configuration": {
                        "text": "The quick brown fox jumps over the lazy dog repeatedly until it gets tired.",
                        "provider": "local",
                    },
                },
                {
                    "step_order": 2,
                    "step_type": "ai_classify",
                    "configuration": {
                        "text": "{{ steps.ai_summarize.summary }}",
                        "labels": ["animal", "technology", "finance"],
                        "provider": "local",
                    },
                },
                {
                    "step_order": 3,
                    "step_type": "notify",
                    "configuration": {
                        "channel": "email",
                        "recipient": "recipient@example.com",
                        "message": "Step 2 output category is {{ steps.ai_classify.category }}",
                    },
                },
                {
                    "step_order": 4,
                    "step_type": "approval",
                    "configuration": {
                        "message": "Approve this execution: {{ payload.custom_field }}",
                    },
                },
            ],
        }

        create_resp = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        assert create_resp.status_code == 201
        workflow_id = create_resp.json()["data"]["id"]

        # Execute workflow
        exec_payload = {"payload": {"custom_field": "invoice-999"}}
        exec_resp = client.post(f"/api/v1/workflows/{workflow_id}/execute", json=exec_payload, headers=headers)
        assert exec_resp.status_code == 200

        data = exec_resp.json()["data"]
        assert data["status"] == "completed"
        assert data["workflow_id"] == workflow_id
        assert len(data["step_executions"]) == 4

        # Validate step executions sorted by creation order
        step_execs = sorted(data["step_executions"], key=lambda x: x["created_at"])
        
        # Validate step 1 (ai_summarize)
        assert step_execs[0]["status"] == "completed"
        assert "summary" in step_execs[0]["results"]
        assert step_execs[0]["duration_sec"] >= 0

        # Validate step 2 (ai_classify)
        assert step_execs[1]["status"] == "completed"
        assert step_execs[1]["results"]["category"] == "animal"

        # Validate step 3 (notify)
        assert step_execs[2]["status"] == "completed"
        assert step_execs[2]["results"]["recipient"] == "recipient@example.com"
        assert "animal" in step_execs[2]["results"]["message"]

        # Validate step 4 (approval)
        assert step_execs[3]["status"] == "completed"
        assert "invoice-999" in step_execs[3]["results"]["message"]


def test_failure_isolation_and_retry():
    email = f"user-{uuid4().hex}@example.com"
    password = "StrongPass123"

    with TestClient(app) as client:
        # Register and login
        client.post(
            "/api/v1/auth/register",
            json={"name": "Engine Tester 2", "email": email, "password": password},
        )
        login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        token = login_resp.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a workflow where step 1 fails but continues, step 2 fails and stops
        workflow_data = {
            "name": "Failure Isolation Workflow",
            "description": "Tests retry and failure isolation",
            "trigger_type": "manual",
            "steps": [
                {
                    "step_order": 1,
                    "step_type": "webhook_call",
                    "configuration": {
                        "url": "http://invalid-url-that-will-definitely-fail.xyz",
                        "max_retries": 2,
                        "backoff_factor": 0.01,  # short delay for fast test
                        "continue_on_error": True,
                    },
                },
                {
                    "step_order": 2,
                    "step_type": "ai_summarize",
                    "configuration": {
                        "text": "",  # will trigger validation error in summarize handler
                        "continue_on_error": False,
                    },
                },
            ],
        }

        create_resp = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
        assert create_resp.status_code == 201
        workflow_id = create_resp.json()["data"]["id"]

        # Execute workflow
        exec_resp = client.post(f"/api/v1/workflows/{workflow_id}/execute", json={}, headers=headers)
        assert exec_resp.status_code == 200

        data = exec_resp.json()["data"]
        assert data["status"] == "failed"  # Failed because step 2 continue_on_error is False

        step_execs = sorted(data["step_executions"], key=lambda x: x["step_id"])
        # Step 1 (webhook_call)
        step_webhook = next(s for s in step_execs if s["retry_count"] > 0)
        assert step_webhook["status"] == "failed"
        assert step_webhook["retry_count"] == 2  # max_retries was 2
        assert step_webhook["failure_reason"] is not None

        # Step 2 (ai_summarize)
        step_sum = next(s for s in step_execs if s["retry_count"] == 0)
        assert step_sum["status"] == "failed"
        assert "text is missing" in step_sum["failure_reason"].lower() or "input 'text' is missing" in step_sum["failure_reason"].lower()
