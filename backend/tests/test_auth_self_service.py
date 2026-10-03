"""Tests for self-service account permanent delete and reactivation."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestAuthSelfService:

    def test_deactivate_and_reactivate_flow(self, client: TestClient) -> None:
        email = f"self_{uuid.uuid4().hex[:6]}@example.com"
        password = "ValidPassword123!"

        # Register
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert reg.status_code == 201

        # Login
        tok_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = tok_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Deactivate
        deact = client.delete("/api/v1/auth/me", headers=headers)
        assert deact.status_code == 200

        # Login should now fail (401 because inactive)
        login_fail = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert login_fail.status_code == 401

        # Reactivate with wrong password fails
        react_fail = client.post("/api/v1/auth/reactivate", json={"email": email, "password": "WrongPassword!"})
        assert react_fail.status_code == 400

        # Reactivate with correct password succeeds
        react_ok = client.post("/api/v1/auth/reactivate", json={"email": email, "password": password})
        assert react_ok.status_code == 200
        new_token = react_ok.json()["access_token"]

        # Now /me works with new token
        me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
        assert me_res.status_code == 200
        assert me_res.json()["is_active"] is True

    def test_permanent_delete_flow(self, client: TestClient) -> None:
        email = f"del_{uuid.uuid4().hex[:6]}@example.com"
        password = "ValidPassword123!"

        client.post("/api/v1/auth/register", json={"email": email, "password": password})
        tok_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = tok_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Delete permanently
        perm_res = client.delete("/api/v1/auth/me/permanent", headers=headers)
        assert perm_res.status_code == 200
        assert "permanently deleted" in perm_res.json()["message"]

        # Login should now fail
        login_fail = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert login_fail.status_code == 401
