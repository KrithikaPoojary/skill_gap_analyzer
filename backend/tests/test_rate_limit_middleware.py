"""Tests for RateLimitMiddleware."""
from __future__ import annotations

from fastapi import FastAPI
from starlette.testclient import TestClient

from app.middleware.rate_limit import RateLimitMiddleware


def test_rate_limit_allows_under_limit():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=5, window_seconds=10)

    @app.get("/test-endpoint")
    def sample():
        return {"ok": True}

    client = TestClient(app)
    for i in range(5):
        resp = client.get("/test-endpoint")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers


def test_rate_limit_blocks_exceeding():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=10)

    @app.get("/test-endpoint")
    def sample():
        return {"ok": True}

    client = TestClient(app)
    for _ in range(3):
        assert client.get("/test-endpoint").status_code == 200

    resp = client.get("/test-endpoint")
    assert resp.status_code == 429
    assert resp.headers.get("retry-after") == "10"
    assert "Rate limit exceeded" in resp.json()["detail"]


def test_rate_limit_exempt_path():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=1, window_seconds=10, exempt_paths={"/api/v1/health"})

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    for _ in range(5):
        assert client.get("/api/v1/health").status_code == 200
