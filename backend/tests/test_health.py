"""Test suite for the /api/v1/health endpoint.

Covers:
- HTTP 200 response and correct Content-Type header.
- Mandatory fields in the response payload.
- Correct static values (status, app_name, version, environment).
- Timestamp is present and formatted as ISO 8601 UTC.
- Application settings consistency via the settings singleton.
"""

from datetime import datetime

import pytest
from httpx import Client

from app.core.config import settings


class TestHealthEndpoint:
    """Grouped tests for the GET /api/v1/health endpoint."""

    ENDPOINT = "/api/v1/health"

    def test_health_returns_http_200(self, client: Client) -> None:
        """Endpoint must return HTTP 200 OK."""
        response = client.get(self.ENDPOINT)
        assert response.status_code == 200

    def test_health_returns_json_content_type(self, client: Client) -> None:
        """Response Content-Type header must indicate JSON."""
        response = client.get(self.ENDPOINT)
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_status_is_healthy(self, client: Client) -> None:
        """The 'status' field must equal 'healthy'."""
        response = client.get(self.ENDPOINT)
        assert response.json()["status"] == "healthy"

    def test_health_app_name_matches_settings(self, client: Client) -> None:
        """The 'app_name' field must match settings.app_name."""
        response = client.get(self.ENDPOINT)
        assert response.json()["app_name"] == settings.app_name

    def test_health_version_matches_settings(self, client: Client) -> None:
        """The 'version' field must match settings.app_version."""
        response = client.get(self.ENDPOINT)
        assert response.json()["version"] == settings.app_version

    def test_health_environment_field_present(self, client: Client) -> None:
        """The 'environment' field must be present in the response payload."""
        response = client.get(self.ENDPOINT)
        assert "environment" in response.json()

    def test_health_timestamp_is_valid_iso8601(self, client: Client) -> None:
        """The 'timestamp' field must be parseable as an ISO 8601 datetime."""
        response = client.get(self.ENDPOINT)
        timestamp_str = response.json().get("timestamp")
        assert timestamp_str is not None, "timestamp field missing from response"
        # fromisoformat handles both UTC 'Z' suffix and '+00:00' offset
        parsed = datetime.fromisoformat(timestamp_str)
        assert parsed is not None

    def test_health_payload_has_all_required_keys(self, client: Client) -> None:
        """Response payload must contain all five mandatory keys."""
        required_keys = {"status", "app_name", "version", "environment", "timestamp"}
        response = client.get(self.ENDPOINT)
        assert required_keys.issubset(response.json().keys())

    def test_health_endpoint_is_idempotent(self, client: Client) -> None:
        """Calling the health endpoint twice must return the same static fields."""
        r1 = client.get(self.ENDPOINT).json()
        r2 = client.get(self.ENDPOINT).json()
        assert r1["status"] == r2["status"]
        assert r1["app_name"] == r2["app_name"]
        assert r1["version"] == r2["version"]
