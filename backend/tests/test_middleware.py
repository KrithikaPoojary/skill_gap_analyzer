"""Tests for request timing and correlation ID middleware.

Verifies:
- X-Process-Time-Ms header is present on every response.
- X-Process-Time-Ms value is a valid positive float.
- X-Request-ID header is always set in the response.
- Client-supplied X-Request-ID is echoed back unchanged.
- Auto-generated X-Request-ID looks like a UUID4.
"""

import re
import uuid

import pytest
from starlette.testclient import TestClient


UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


class TestTimingMiddleware:
    """Validate the RequestTimingMiddleware behaviour."""

    def test_timing_header_present(self, client: TestClient) -> None:
        """Every response must include X-Process-Time-Ms."""
        response = client.get("/api/v1/health")
        assert "x-process-time-ms" in response.headers

    def test_timing_header_is_positive_float(self, client: TestClient) -> None:
        """X-Process-Time-Ms must be parseable as a positive float."""
        header_value = client.get("/api/v1/health").headers["x-process-time-ms"]
        elapsed = float(header_value)
        assert elapsed >= 0.0

    def test_timing_header_on_404(self, client: TestClient) -> None:
        """Timing header must be present even on 404 error responses."""
        response = client.get("/api/v1/nonexistent")
        assert "x-process-time-ms" in response.headers


class TestCorrelationIdMiddleware:
    """Validate the CorrelationIdMiddleware behaviour."""

    def test_request_id_header_present(self, client: TestClient) -> None:
        """Every response must include X-Request-ID."""
        response = client.get("/api/v1/health")
        assert "x-request-id" in response.headers

    def test_auto_generated_request_id_is_uuid4(self, client: TestClient) -> None:
        """Auto-generated X-Request-ID must match UUID4 format."""
        request_id = client.get("/api/v1/health").headers["x-request-id"]
        assert UUID4_PATTERN.match(request_id), f"Not a UUID4: {request_id}"

    def test_client_supplied_request_id_is_echoed(self, client: TestClient) -> None:
        """If client sends X-Request-ID, it must be returned unchanged."""
        custom_id = "my-trace-id-99999"
        response = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
        assert response.headers["x-request-id"] == custom_id

    def test_different_requests_get_different_ids(self, client: TestClient) -> None:
        """Without a client ID, each request must receive a unique generated ID."""
        id1 = client.get("/api/v1/health").headers["x-request-id"]
        id2 = client.get("/api/v1/health").headers["x-request-id"]
        assert id1 != id2
