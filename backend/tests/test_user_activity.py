"""Tests for user login activity tracking and metrics."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestUserActivityTracking:

    def test_login_increments_login_count_and_sets_last_login(self, client: TestClient) -> None:
        email = f"activity_{uuid.uuid4().hex[:6]}@example.com"
        password = "SecurePass123!"

        # Register user
        reg_res = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Activity Tester"},
        )
        assert reg_res.status_code == 201
        registered_data = reg_res.json()
        assert registered_data["login_count"] == 0
        assert registered_data["last_login_at"] is None

        # First login
        login_res1 = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert login_res1.status_code == 200
        token1 = login_res1.json()["access_token"]

        # Fetch /me
        me_res1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token1}"},
        )
        assert me_res1.status_code == 200
        data1 = me_res1.json()
        assert data1["login_count"] == 1
        assert data1["last_login_at"] is not None
        first_login_time = data1["last_login_at"]

        # Second login
        login_res2 = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        )
        assert login_res2.status_code == 200
        token2 = login_res2.json()["access_token"]

        # Fetch /me again
        me_res2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token2}"},
        )
        assert me_res2.status_code == 200
        data2 = me_res2.json()
        assert data2["login_count"] == 2
        assert data2["last_login_at"] is not None
        assert data2["last_login_at"] >= first_login_time
