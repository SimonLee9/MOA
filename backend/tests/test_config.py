"""
Configuration Tests
"""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.config import Settings, ConfigurationError


class TestSettingsValidation:
    """Tests for Settings validation."""

    def test_valid_settings(self):
        """Test valid settings creation."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
        )

        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/db"
        assert settings.environment == "development"

    def test_database_url_required(self):
        """Test database URL is required."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                jwt_secret_key="a" * 32,
                minio_access_key="key",
                minio_secret_key="secret",
            )

        assert "database_url" in str(exc_info.value).lower()

    def test_database_url_format_postgresql(self):
        """Test PostgreSQL database URL is valid."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
        )
        assert "postgresql" in settings.database_url

    def test_database_url_format_sqlite(self):
        """Test SQLite database URL is valid."""
        settings = Settings(
            database_url="sqlite+aiosqlite:///./test.db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
        )
        assert "sqlite" in settings.database_url

    def test_database_url_invalid_format(self):
        """Test invalid database URL format."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                database_url="mysql://user:pass@localhost/db",
                jwt_secret_key="a" * 32,
                minio_access_key="key",
                minio_secret_key="secret",
            )

        assert "DATABASE_URL must start with" in str(exc_info.value)

    def test_jwt_secret_required(self):
        """Test JWT secret key is required."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                minio_access_key="key",
                minio_secret_key="secret",
            )

        assert "jwt_secret_key" in str(exc_info.value).lower()

    def test_jwt_secret_minimum_length(self):
        """Test JWT secret minimum length."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                jwt_secret_key="short",
                minio_access_key="key",
                minio_secret_key="secret",
            )

        assert "32 characters" in str(exc_info.value)

    def test_redis_url_format(self):
        """Test Redis URL validation."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            redis_url="redis://localhost:6379",
            minio_access_key="key",
            minio_secret_key="secret",
        )
        assert settings.redis_url == "redis://localhost:6379"

    def test_redis_url_ssl(self):
        """Test Redis URL with SSL."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            redis_url="rediss://localhost:6379",
            minio_access_key="key",
            minio_secret_key="secret",
        )
        assert settings.redis_url.startswith("rediss://")

    def test_redis_url_invalid(self):
        """Test invalid Redis URL."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                jwt_secret_key="a" * 32,
                redis_url="http://localhost:6379",
                minio_access_key="key",
                minio_secret_key="secret",
            )

        assert "redis://" in str(exc_info.value)


class TestProductionValidation:
    """Tests for production environment validation."""

    def test_production_requires_claude_api(self):
        """Test production requires Claude API key."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment="production",
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                jwt_secret_key="a" * 32,
                minio_access_key="key",
                minio_secret_key="secret",
                claude_api_key="",  # Missing
            )

        assert "CLAUDE_API_KEY is required" in str(exc_info.value)

    def test_production_debug_must_be_false(self):
        """Test production requires debug=False."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                environment="production",
                debug=True,
                database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
                jwt_secret_key="a" * 32,
                minio_access_key="key",
                minio_secret_key="secret",
                claude_api_key="sk-test",
            )

        assert "DEBUG must be False" in str(exc_info.value)

    def test_production_valid_settings(self):
        """Test valid production settings."""
        settings = Settings(
            environment="production",
            debug=False,
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            claude_api_key="sk-test-key",
        )

        assert settings.is_production is True
        assert settings.debug is False

    def test_development_allows_missing_claude_key(self):
        """Test development allows missing Claude API key."""
        settings = Settings(
            environment="development",
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            claude_api_key="",  # OK in development
        )

        assert settings.is_production is False


class TestCorsOrigins:
    """Tests for CORS origins parsing."""

    def test_single_origin(self):
        """Test single CORS origin."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            cors_origins="http://localhost:3000",
        )

        assert settings.cors_origins_list == ["http://localhost:3000"]

    def test_multiple_origins(self):
        """Test multiple CORS origins."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            cors_origins="http://localhost:3000, https://app.example.com",
        )

        assert len(settings.cors_origins_list) == 2
        assert "http://localhost:3000" in settings.cors_origins_list
        assert "https://app.example.com" in settings.cors_origins_list


class TestOptionalServicesCheck:
    """Tests for optional services status check."""

    def test_check_services_all_configured(self):
        """Test all services configured."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            claude_api_key="sk-test",
            clova_api_key="clova-key",
            clova_api_secret="clova-secret",
        )

        status = settings.check_optional_services()

        assert status["claude_api"]["configured"] is True
        assert status["clova_stt"]["configured"] is True
        assert status["minio"]["configured"] is True

    def test_check_services_missing_claude(self):
        """Test Claude API not configured."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            claude_api_key="",
        )

        status = settings.check_optional_services()

        assert status["claude_api"]["configured"] is False
        assert "summarization" in status["claude_api"]["required_for"]

    def test_check_services_missing_clova(self):
        """Test Clova STT not configured."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
            clova_api_key="",
            clova_api_secret="",
        )

        status = settings.check_optional_services()

        assert status["clova_stt"]["configured"] is False
        assert "speech_to_text" in status["clova_stt"]["required_for"]


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_default_app_name(self):
        """Test default app name."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
        )

        assert settings.app_name == "MOA API"

    def test_default_debug_false(self):
        """Test debug defaults to False."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
        )

        assert settings.debug is False

    def test_default_token_expiry(self):
        """Test default token expiry times."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
        )

        assert settings.access_token_expire_minutes == 30
        assert settings.refresh_token_expire_days == 7

    def test_default_minio_bucket(self):
        """Test default MinIO bucket name."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/db",
            jwt_secret_key="a" * 32,
            minio_access_key="key",
            minio_secret_key="secret",
        )

        assert settings.minio_bucket == "moa-audio"
