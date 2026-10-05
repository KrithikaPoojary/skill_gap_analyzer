"""Tests for notification bulk-read, profile completeness, and profile skill by ID endpoints."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import engine
from app.models.notification import Notification
from app.models.skill import Skill
from app.models.associations import UserSkill
from sqlalchemy.orm import Session


class TestNotificationBulkRead:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        uid = uuid.uuid4().hex[:6]
        email = f"bulkread_{uid}@example.com"
        password = "Password123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": f"Bulk User {uid}"},
        )
        user_id = reg.json()["id"]
        token = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        ).json()["access_token"]
        return user_id, token

    def test_bulk_read_requires_auth(self, client: TestClient) -> None:
        res = client.patch("/api/v1/notifications/bulk-read", json={"notification_ids": [1, 2]})
        assert res.status_code == 401

    def test_bulk_read_empty_list_rejected(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        res = client.patch(
            "/api/v1/notifications/bulk-read",
            json={"notification_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400

    def test_bulk_read_marks_notifications(self, client: TestClient) -> None:
        user_id, token = self._register_and_login(client)

        # Create notifications directly
        with Session(engine) as db:
            n1 = Notification(user_id=user_id, title="N1", message="msg1", category="general")
            n2 = Notification(user_id=user_id, title="N2", message="msg2", category="general")
            n3 = Notification(user_id=user_id, title="N3", message="msg3", category="general")
            db.add_all([n1, n2, n3])
            db.commit()
            ids = [n1.id, n2.id]

        res = client.patch(
            "/api/v1/notifications/bulk-read",
            json={"notification_ids": ids},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["marked_read"] == 2


class TestProfileCompleteness:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        uid = uuid.uuid4().hex[:6]
        email = f"complete_{uid}@example.com"
        password = "Password123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": f"Complete User {uid}"},
        )
        user_id = reg.json()["id"]
        token = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        ).json()["access_token"]
        return user_id, token

    def test_completeness_requires_auth(self, client: TestClient) -> None:
        res = client.get("/api/v1/profile/me/completeness")
        assert res.status_code == 401

    def test_completeness_new_user(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        res = client.get(
            "/api/v1/profile/me/completeness",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "completeness_pct" in data
        assert "checklist" in data
        assert isinstance(data["checklist"], dict)
        # New user should not be 100% complete
        assert data["completeness_pct"] < 100.0

    def test_completeness_increases_after_profile_update(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        before = client.get("/api/v1/profile/me/completeness", headers=headers).json()["data"]["completeness_pct"]

        # Update profile with more fields
        client.put(
            "/api/v1/profile/me",
            json={
                "headline": "Software Engineer",
                "bio": "Passionate developer",
                "current_title": "Engineer",
                "location": "Bangalore",
                "years_of_experience": 3.0,
            },
            headers=headers,
        )

        after = client.get("/api/v1/profile/me/completeness", headers=headers).json()["data"]["completeness_pct"]
        assert after > before


class TestProfileSkillById:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        uid = uuid.uuid4().hex[:6]
        email = f"skillbyid_{uid}@example.com"
        password = "Password123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": f"SkillById User {uid}"},
        )
        user_id = reg.json()["id"]
        token = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        ).json()["access_token"]
        return user_id, token

    def test_skill_by_id_not_found(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)
        res = client.get(
            "/api/v1/profile/me/skills/999999",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404

    def test_skill_by_id_returns_skill(self, client: TestClient) -> None:
        user_id, token = self._register_and_login(client)
        headers = {"Authorization": f"Bearer {token}"}

        uid = uuid.uuid4().hex[:6]
        with Session(engine) as db:
            skill = Skill(
                name=f"SkillById Test {uid}",
                normalized_name=f"skillbyid_test_{uid}",
                category="Testing",
            )
            db.add(skill)
            db.commit()
            skill_id = skill.id

            us = UserSkill(
                user_id=user_id,
                skill_id=skill_id,
                proficiency_level="intermediate",
                years_of_experience=2.0,
            )
            db.add(us)
            db.commit()

        res = client.get(
            f"/api/v1/profile/me/skills/{skill_id}",
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["skill_id"] == skill_id
        assert data["proficiency_level"] == "intermediate"
