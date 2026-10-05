"""Tests for notification category filtering and GET /notifications/stats endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.models.notification import Notification
from sqlalchemy.orm import Session


class TestNotificationsStats:

    def _login_user(self, client: TestClient) -> tuple[int, str]:
        email = f"notif_stats_{uuid.uuid4().hex[:6]}@example.com"
        reg = client.post("/api/v1/auth/register", json={"email": email, "password": "Password123!"})
        uid = reg.json()["id"]
        tok = client.post("/api/v1/auth/login", data={"username": email, "password": "Password123!"}).json()["access_token"]
        return uid, tok

    def test_notification_stats_and_filtering(self, client: TestClient) -> None:
        user_id, token = self._login_user(client)
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Empty stats
        res_empty = client.get("/api/v1/notifications/stats", headers=headers)
        assert res_empty.status_code == 200
        data_empty = res_empty.json()
        assert data_empty["total"] == 0
        assert data_empty["unread"] == 0
        assert data_empty["read"] == 0

        # 2. Add notifications in different categories and read states
        with Session(engine) as db:
            n1 = Notification(user_id=user_id, title="Job Alert", message="New matching job", category="job_alert", is_read=False)
            n2 = Notification(user_id=user_id, title="Roadmap Step", message="Phase 1 completed", category="roadmap", is_read=True)
            n3 = Notification(user_id=user_id, title="Skill Verified", message="Python skill verified", category="skill", is_read=False)
            db.add_all([n1, n2, n3])
            db.commit()

        # 3. Verify stats
        res_stats = client.get("/api/v1/notifications/stats", headers=headers)
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["total"] == 3
        assert stats["unread"] == 2
        assert stats["read"] == 1
        assert "job_alert" in stats["by_category"]
        assert stats["by_category"]["job_alert"]["unread"] == 1
        assert stats["by_category"]["roadmap"]["read"] == 1

        # 4. Filter by category
        res_filtered = client.get("/api/v1/notifications?category=job_alert", headers=headers)
        assert res_filtered.status_code == 200
        items = res_filtered.json()
        assert len(items) == 1
        assert items[0]["category"] == "job_alert"
