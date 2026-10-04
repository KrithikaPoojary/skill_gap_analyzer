"""Tests for GET /analytics/summary endpoint."""
from __future__ import annotations

from starlette.testclient import TestClient


class TestAnalyticsSummary:

    def test_get_analytics_summary_success(self, client: TestClient) -> None:
        res = client.get("/api/v1/analytics/summary")
        assert res.status_code == 200
        data = res.json()["data"]
        assert "active_jobs" in data
        assert "total_skills" in data
        assert "total_target_roles" in data
        assert "total_active_users" in data
        assert "remote_job_ratio_pct" in data
        assert isinstance(data["active_jobs"], int)
        assert isinstance(data["total_skills"], int)
