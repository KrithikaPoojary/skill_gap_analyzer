"""Tests for notifications unread-count endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.services import notification_service


class TestNotificationsUnreadCount:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"unread_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_get_unread_count(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # Initially 0 unread
        res0 = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert res0.status_code == 200
        assert res0.json()["unread_count"] == 0

        # Add 2 notifications
        with SessionLocal() as db:
            n1 = notification_service.create_notification(
                db, user_id=user_id, title="Welcome", message="Hello 1"
            )
            n2 = notification_service.create_notification(
                db, user_id=user_id, title="Update", message="Hello 2"
            )

        res2 = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert res2.status_code == 200
        assert res2.json()["unread_count"] == 2

        # Mark 1 as read
        with SessionLocal() as db:
            notification_service.mark_read(db, notification_id=n2.id, user_id=user_id)

        res1 = client.get("/api/v1/notifications/unread-count", headers=headers)
        assert res1.status_code == 200
        assert res1.json()["unread_count"] == 1
