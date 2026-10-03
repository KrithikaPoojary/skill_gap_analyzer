"""Tests for expanded profile stats endpoint."""
from __future__ import annotations

import uuid
from starlette.testclient import TestClient


class TestProfileStatsExpanded:

    def test_profile_stats_includes_extended_fields(self, client: TestClient) -> None:
        email = f"stats_{uuid.uuid4().hex[:6]}@example.com"
        password = "Password123!"

        # Register
        client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Stats User"})

        # Login
        tok_res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
        token = tok_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get stats
        stats_res = client.get("/api/v1/profile/me/stats", headers=headers)
        assert stats_res.status_code == 200
        data = stats_res.json()["data"]

        # All extended fields should be present
        assert "total_skills" in data
        assert "avg_proficiency_score" in data
        assert "profile_complete" in data
        assert "roadmap_count" in data
        assert "snapshot_count" in data
        assert "login_count" in data
        assert "last_login_at" in data

        # login_count should be 1 after our first login above
        assert data["login_count"] == 1
        # roadmap_count and snapshot_count for a new user are 0
        assert data["roadmap_count"] == 0
        assert data["snapshot_count"] == 0
