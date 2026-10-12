"""Tests for job location statistics endpoint."""

from starlette.testclient import TestClient


class TestJobLocationStats:
    """Tests for GET /api/v1/analytics/jobs/by-location."""

    def test_location_stats_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/jobs/by-location")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        data = payload["data"]
        assert "locations" in data
        assert "total_with_location" in data
        assert isinstance(data["locations"], list)

    def test_location_stats_with_limit(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/jobs/by-location?limit=3")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["locations"]) <= 3

    def test_location_entry_shape(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/jobs/by-location")
        data = resp.json()["data"]
        if data["locations"]:
            loc = data["locations"][0]
            assert "location" in loc
            assert "count" in loc
            assert "percentage" in loc


class TestJobEmploymentTypeStats:
    """Tests for GET /api/v1/analytics/jobs/by-employment-type."""

    def test_employment_type_stats_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/v1/analytics/jobs/by-employment-type")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["success"] is True
        data = payload["data"]
        assert "types" in data
        assert "total" in data
        assert isinstance(data["types"], list)

