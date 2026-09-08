"""Test suite for the FastAPI application factory.

Covers:
- The ``create_application()`` factory produces a valid FastAPI instance.
- Application title, version, and description match settings.
- OpenAPI schema endpoint is accessible.
- Interactive docs endpoint is accessible.
"""

from fastapi import FastAPI

from app.core.config import settings
from app.main import app, create_application


class TestApplicationFactory:
    """Validate the FastAPI application factory configuration."""

    def test_create_application_returns_fastapi_instance(self) -> None:
        """``create_application()`` must return a FastAPI instance."""
        instance = create_application()
        assert isinstance(instance, FastAPI)

    def test_app_module_singleton_is_fastapi_instance(self) -> None:
        """The module-level ``app`` object must be a FastAPI instance."""
        assert isinstance(app, FastAPI)

    def test_app_title_matches_settings(self) -> None:
        """FastAPI title must match ``settings.app_name``."""
        assert app.title == settings.app_name

    def test_app_version_matches_settings(self) -> None:
        """FastAPI version must match ``settings.app_version``."""
        assert app.version == settings.app_version

    def test_openapi_schema_endpoint_accessible(self, client) -> None:
        """The /openapi.json endpoint must return HTTP 200."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_schema_contains_health_route(self, client) -> None:
        """The OpenAPI schema must document the /api/v1/health path."""
        schema = client.get("/openapi.json").json()
        paths = schema.get("paths", {})
        assert "/api/v1/health" in paths

    def test_swagger_docs_endpoint_accessible(self, client) -> None:
        """The /docs Swagger UI endpoint must return HTTP 200."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_cors_middleware_allows_configured_origins(self, client) -> None:
        """CORS preflight from a configured origin must be accepted."""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        # 200 or 204 indicates the middleware allowed the preflight
        assert response.status_code in (200, 204)
