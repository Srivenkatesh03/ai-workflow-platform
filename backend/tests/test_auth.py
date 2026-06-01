from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_register_login_and_current_user():
    email = f"user-{uuid4().hex}@example.com"
    password = "StrongPass123"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/v1/auth/register",
            json={"name": "Test User", "email": email, "password": password},
        )
        assert register_response.status_code == 201
        register_payload = register_response.json()["data"]
        assert register_payload["user"]["email"] == email
        assert register_payload["user"]["role"] == "operator"
        assert register_payload["access_token"]
        assert register_payload["refresh_token"]

        login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_response.status_code == 200
        access_token = login_response.json()["data"]["access_token"]

        me_response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_response.status_code == 200
        assert me_response.json()["data"]["email"] == email


def test_protected_route_requires_token():
    with TestClient(app) as client:
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401
