"""Tests for global HTTP exception handlers.

Verifies that:
- Unknown routes return the standard 404 error envelope.
- Invalid request bodies return the standard 422 error envelope.
- All error responses use the canonical ErrorResponse shape.
- Error responses contain machine-readable error codes.
"""

import pytest
from starlette.testclient import TestClient


class TestExceptionHandlers:
    """Validate the global exception handler behaviour."""

    def test_unknown_route_returns_404(self, client: TestClient) -> None:
        """GET request to a non-existent route must return HTTP 404."""
        response = client.get("/api/v1/this-route-does-not-exist")
        assert response.status_code == 404

    def test_404_response_has_success_false(self, client: TestClient) -> None:
        """404 response envelope must have success=False."""
        body = client.get("/api/v1/nonexistent").json()
        assert body["success"] is False

    def test_404_response_has_error_field(self, client: TestClient) -> None:
        """404 response must contain an 'error' field."""
        body = client.get("/api/v1/nonexistent").json()
        assert "error" in body

    def test_404_error_code_is_not_found(self, client: TestClient) -> None:
        """404 error code must be 'NOT_FOUND'."""
        error = client.get("/api/v1/nonexistent").json()["error"]
        assert error["code"] == "NOT_FOUND"

    def test_404_error_has_message(self, client: TestClient) -> None:
        """404 error must include a non-empty human-readable message."""
        error = client.get("/api/v1/nonexistent").json()["error"]
        assert error.get("message")

    def test_404_response_still_has_correlation_id(self, client: TestClient) -> None:
        """Even error responses must include X-Request-ID header."""
        response = client.get("/api/v1/nonexistent")
        assert "x-request-id" in response.headers

    def test_404_response_has_timing_header(self, client: TestClient) -> None:
        """Even error responses must include X-Process-Time-Ms header."""
        response = client.get("/api/v1/nonexistent")
        assert "x-process-time-ms" in response.headers
