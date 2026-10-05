"""Tests for GET /gap-analysis/me/snapshot/latest endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.db.session import engine
from app.models.gap_snapshot import SkillGapSnapshot
from sqlalchemy.orm import Session


class TestGapSnapshotLatest:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        uid = uuid.uuid4().hex[:6]
        email = f"snaplatest_{uid}@example.com"
        password = "Password123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": f"Snap User {uid}"},
        )
        user_id = reg.json()["id"]
        token = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        ).json()["access_token"]
        return user_id, token

    def test_snapshot_latest_unauthenticated(self, client: TestClient) -> None:
        res = client.get("/api/v1/gap-analysis/me/snapshot/latest")
        assert res.status_code == 401

    def test_snapshot_latest_not_found(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)

        res = client.get(
            "/api/v1/gap-analysis/me/snapshot/latest",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 404

    def test_snapshot_latest_returns_most_recent(self, client: TestClient) -> None:
        user_id, token = self._register_and_login(client)

        # Seed two snapshots for this user
        with Session(engine) as db:
            s1 = SkillGapSnapshot(
                user_id=user_id,
                role_id=None,
                role_title="Old Role",
                readiness_score=30.0,
                matched_skills=[],
                missing_skills=[],
            )
            db.add(s1)
            db.commit()

            s2 = SkillGapSnapshot(
                user_id=user_id,
                role_id=None,
                role_title="New Role",
                readiness_score=75.0,
                matched_skills=[],
                missing_skills=[],
            )
            db.add(s2)
            db.commit()

        res = client.get(
            "/api/v1/gap-analysis/me/snapshot/latest",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()["data"]
        # Should return the most recent snapshot (s2 added last)
        assert data["role_title"] == "New Role"
        assert data["readiness_score"] == 75.0
