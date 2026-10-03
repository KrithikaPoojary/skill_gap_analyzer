"""Tests for bulk notifications endpoints."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import SessionLocal
from app.services import notification_service


class TestNotificationsBulk:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"notif_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_clear_read_and_clear_all_notifications(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        with SessionLocal() as db:
            n1 = notification_service.create_notification(db, user_id=user_id, title="Test 1", message="Body 1")
            n2 = notification_service.create_notification(db, user_id=user_id, title="Test 2", message="Body 2")
            n3 = notification_service.create_notification(db, user_id=user_id, title="Test 3", message="Body 3")
            # Mark n1 as read
            notification_service.mark_read(db, notification_id=n1.id, user_id=user_id)

        # Clear read notifications
        res_read = client.delete("/api/v1/notifications/clear-read", headers=headers)
        assert res_read.status_code == 200
        assert res_read.json()["deleted_count"] == 1

        # Check remaining notifications (should be 2)
        res_list = client.get("/api/v1/notifications", headers=headers)
        assert res_list.status_code == 200
        assert len(res_list.json()) == 2

        # Clear all
        res_all = client.delete("/api/v1/notifications/clear-all", headers=headers)
        assert res_all.status_code == 200
        assert res_all.json()["deleted_count"] == 2

        # Check list is now empty
        res_empty = client.get("/api/v1/notifications", headers=headers)
        assert res_empty.status_code == 200
        assert len(res_empty.json()) == 0
