"""Tests for /notifications endpoints."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestNotificationsEndpoints:

    def _register_and_login(self, client: TestClient) -> str:
        email = f"n{uuid.uuid4().hex[:6]}@test.com"
        client.post("/api/v1/auth/register", json={"email": email, "password": "Test1234!"})
        resp = client.post("/api/v1/auth/login", data={"username": email, "password": "Test1234!"})
        return resp.json()["access_token"]

    def test_list_notifications_unauthenticated(self, client: TestClient) -> None:
        resp = client.get("/api/v1/notifications")
        assert resp.status_code == 401

    def test_list_notifications_empty(self, client: TestClient) -> None:
        token = self._register_and_login(client)
        resp = client.get(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_mark_all_read_empty(self, client: TestClient) -> None:
        token = self._register_and_login(client)
        resp = client.patch(
            "/api/v1/notifications/read-all",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["marked_read"] == 0

    def test_mark_nonexistent_read_returns_404(self, client: TestClient) -> None:
        token = self._register_and_login(client)
        resp = client.patch(
            "/api/v1/notifications/999999/read",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient) -> None:
        token = self._register_and_login(client)
        resp = client.delete(
            "/api/v1/notifications/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404
