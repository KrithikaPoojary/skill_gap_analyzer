"""Test suite for the /api/v1/health endpoint.

Day 2 update: health response is now wrapped in the APIResponse envelope,
so assertions check the outer ``success``/``data`` structure as well as
the inner payload fields.
"""

from datetime import datetime

import pytest
from starlette.testclient import TestClient

from app.core.config import settings


class TestHealthEndpoint:
    """Grouped tests for GET /api/v1/health."""

    ENDPOINT = "/api/v1/health"

    def test_health_returns_http_200(self, client: TestClient) -> None:
        """Endpoint must return HTTP 200 OK."""
        response = client.get(self.ENDPOINT)
        assert response.status_code == 200

    def test_health_returns_json_content_type(self, client: TestClient) -> None:
        """Response Content-Type must indicate JSON."""
        response = client.get(self.ENDPOINT)
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_envelope_success_is_true(self, client: TestClient) -> None:
        """Outer envelope 'success' field must be True."""
        body = client.get(self.ENDPOINT).json()
        assert body["success"] is True

    def test_health_data_field_present(self, client: TestClient) -> None:
        """Outer envelope must contain a 'data' field."""
        body = client.get(self.ENDPOINT).json()
        assert "data" in body
        assert body["data"] is not None

    def test_health_status_is_healthy(self, client: TestClient) -> None:
        """Inner data.status must equal 'healthy'."""
        data = client.get(self.ENDPOINT).json()["data"]
        assert data["status"] == "healthy"

    def test_health_app_name_matches_settings(self, client: TestClient) -> None:
        """Inner data.app_name must match settings.app_name."""
        data = client.get(self.ENDPOINT).json()["data"]
        assert data["app_name"] == settings.app_name

    def test_health_version_matches_settings(self, client: TestClient) -> None:
        """Inner data.version must match settings.app_version."""
        data = client.get(self.ENDPOINT).json()["data"]
        assert data["version"] == settings.app_version

    def test_health_environment_field_present(self, client: TestClient) -> None:
        """Inner data.environment must be present."""
        data = client.get(self.ENDPOINT).json()["data"]
        assert "environment" in data

    def test_health_timestamp_is_valid_iso8601(self, client: TestClient) -> None:
        """Inner data.timestamp must be parseable as ISO 8601."""
        data = client.get(self.ENDPOINT).json()["data"]
        timestamp_str = data.get("timestamp")
        assert timestamp_str is not None
        parsed = datetime.fromisoformat(timestamp_str)
        assert parsed is not None

    def test_health_response_has_timing_header(self, client: TestClient) -> None:
        """Response must include X-Process-Time-Ms header from timing middleware."""
        response = client.get(self.ENDPOINT)
        assert "x-process-time-ms" in response.headers

    def test_health_response_has_request_id_header(self, client: TestClient) -> None:
        """Response must include X-Request-ID header from correlation middleware."""
        response = client.get(self.ENDPOINT)
        assert "x-request-id" in response.headers

    def test_health_honours_client_request_id(self, client: TestClient) -> None:
        """If client sends X-Request-ID, it must be echoed back unchanged."""
        custom_id = "test-correlation-abc123"
        response = client.get(self.ENDPOINT, headers={"X-Request-ID": custom_id})
        assert response.headers.get("x-request-id") == custom_id
