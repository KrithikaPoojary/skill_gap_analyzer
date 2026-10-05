"""Tests for GET /recommendations/me endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient

from app.models.role import TargetRole
from sqlalchemy.orm import Session
from app.db.session import engine


class TestRecommendationsMe:

    def _register_and_login(self, client: TestClient) -> tuple[int, str]:
        uid = uuid.uuid4().hex[:6]
        email = f"recme_{uid}@example.com"
        password = "Password123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": f"RecMe User {uid}"},
        )
        user_id = reg.json()["id"]
        token = client.post(
            "/api/v1/auth/login",
            data={"username": email, "password": password},
        ).json()["access_token"]
        return user_id, token

    def test_recommendations_me_unauthenticated(self, client: TestClient) -> None:
        res = client.get("/api/v1/recommendations/me")
        assert res.status_code == 401

    def test_recommendations_me_authenticated(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)

        # Create a target role so recommendations have something to rank
        uid = uuid.uuid4().hex[:6]
        with Session(engine) as db:
            role = TargetRole(
                title=f"Recommendation Engineer {uid}",
                slug=f"rec-engineer-{uid}",
                category="Software",
                description="Full-stack software engineering",
                is_active=True,
            )
            db.add(role)
            db.commit()

        res = client.get(
            "/api/v1/recommendations/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert "recommendations" in body["data"]
        assert isinstance(body["data"]["recommendations"], list)

    def test_recommendations_me_limit_param(self, client: TestClient) -> None:
        _, token = self._register_and_login(client)

        res = client.get(
            "/api/v1/recommendations/me?limit=2",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        recs = res.json()["data"]["recommendations"]
        assert len(recs) <= 2
