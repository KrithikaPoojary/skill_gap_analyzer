"""Tests for the FastAPI application factory.

Day 2 update: verifies new OpenAPI tags, middleware registration,
and enriched metadata added to the factory.
"""

from fastapi import FastAPI

from app.core.config import settings
from app.main import app, create_application


class TestApplicationFactory:
    """Validate the FastAPI application factory configuration."""

    def test_create_application_returns_fastapi_instance(self) -> None:
        """create_application() must return a FastAPI instance."""
        instance = create_application()
        assert isinstance(instance, FastAPI)

    def test_app_module_singleton_is_fastapi_instance(self) -> None:
        """The module-level app object must be a FastAPI instance."""
        assert isinstance(app, FastAPI)

    def test_app_title_matches_settings(self) -> None:
        """FastAPI title must match settings.app_name."""
        assert app.title == settings.app_name

    def test_app_version_matches_settings(self) -> None:
        """FastAPI version must match settings.app_version."""
        assert app.version == settings.app_version

    def test_openapi_schema_endpoint_accessible(self, client) -> None:
        """The /openapi.json endpoint must return HTTP 200."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_openapi_schema_contains_health_route(self, client) -> None:
        """The OpenAPI schema must document the /api/v1/health path."""
        schema = client.get("/openapi.json").json()
        assert "/api/v1/health" in schema.get("paths", {})

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
        assert response.status_code in (200, 204)

    def test_openapi_tags_include_system_health(self, client) -> None:
        """OpenAPI schema must declare the 'System Health' tag."""
        schema = client.get("/openapi.json").json()
        tag_names = [t["name"] for t in schema.get("tags", [])]
        assert "System Health" in tag_names

    def test_openapi_tags_include_future_feature_tags(self, client) -> None:
        """OpenAPI schema must pre-declare Jobs, Matching, and Analytics tags."""
        schema = client.get("/openapi.json").json()
        tag_names = [t["name"] for t in schema.get("tags", [])]
        for expected in ("Jobs", "Matching", "Analytics"):
            assert expected in tag_names, f"Tag '{expected}' missing from schema"

    def test_openapi_contact_info_present(self, client) -> None:
        """OpenAPI info block must include contact information."""
        schema = client.get("/openapi.json").json()
        contact = schema.get("info", {}).get("contact")
        assert contact is not None
        assert "name" in contact
