"""Unit tests for the application settings module.

Validates that default values are correct, types are enforced,
and the Settings object is instantiated without errors.
"""

from app.core.config import Settings, settings


class TestSettingsDefaults:
    """Verify default configuration values used in development."""

    def test_settings_singleton_is_importable(self) -> None:
        """The module-level ``settings`` singleton must be a Settings instance."""
        assert isinstance(settings, Settings)

    def test_default_app_name(self) -> None:
        """Default app name must be set."""
        assert "Skill Gap Analyzer" in settings.app_name

    def test_default_app_version(self) -> None:
        """Default version must follow semver pattern."""
        parts = settings.app_version.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_default_environment_is_development(self) -> None:
        """Default environment must be 'development'."""
        assert settings.environment == "development"

    def test_debug_is_true_by_default(self) -> None:
        """Debug mode must be enabled in default (development) configuration."""
        assert settings.debug is True

    def test_api_v1_prefix(self) -> None:
        """API v1 prefix must start with /api/."""
        assert settings.api_v1_prefix.startswith("/api/")

    def test_max_upload_size_is_five_mb(self) -> None:
        """Default upload size limit must be exactly 5 MB (5,242,880 bytes)."""
        assert settings.max_upload_size_bytes == 5 * 1024 * 1024

    def test_allowed_upload_extensions_include_pdf(self) -> None:
        """PDF must be an allowed resume upload extension."""
        assert ".pdf" in settings.allowed_upload_extensions

    def test_database_url_is_set(self) -> None:
        """A non-empty database URL must be configured."""
        assert settings.database_url
        assert len(settings.database_url) > 0

    def test_fresh_settings_instance_uses_defaults(self) -> None:
        """A new Settings() instance must also reflect the same defaults."""
        fresh = Settings()
        assert fresh.environment == "development"
        assert fresh.app_version == settings.app_version
