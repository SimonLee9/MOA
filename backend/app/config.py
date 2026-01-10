"""
MOA Backend Configuration
Uses Pydantic Settings for environment variable management
"""

import logging
import sys
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "MOA API"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # MinIO / S3 Storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "moa-audio"
    minio_use_ssl: bool = False

    # Naver Clova Speech API
    clova_api_key: str = ""
    clova_api_secret: str = ""
    clova_invoke_url: str = "https://clovaspeech-gw.ncloud.com/recog/v1/stt"

    # Claude API
    claude_api_key: str = ""

    # Slack Integration
    slack_webhook_url: str = ""
    slack_default_channel: str = ""

    # Google Calendar Integration
    google_calendar_credentials: str = ""

    # Notion Integration
    notion_api_key: str = ""

    # Jira Integration
    jira_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""

    # JWT Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        if not v:
            raise ValueError("DATABASE_URL is required")

        valid_prefixes = (
            "postgresql://",
            "postgresql+asyncpg://",
            "sqlite+aiosqlite://",
        )
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"DATABASE_URL must start with one of: {', '.join(valid_prefixes)}"
            )
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key"""
        if not v:
            raise ValueError("JWT_SECRET_KEY is required")
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters for security"
            )
        return v

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format"""
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must start with redis:// or rediss://")
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Additional validation for production environment"""
        if self.is_production:
            errors = []

            # Check debug is disabled in production
            if self.debug:
                errors.append("DEBUG must be False in production")

            # Check API keys are set for production features
            if not self.claude_api_key:
                errors.append("CLAUDE_API_KEY is required in production")

            # Check SSL for MinIO in production
            if not self.minio_use_ssl:
                logger.warning("MINIO_USE_SSL is False in production - consider enabling SSL")

            # Check CORS origins don't include localhost in production
            if "localhost" in self.cors_origins.lower():
                logger.warning("CORS_ORIGINS contains localhost in production")

            if errors:
                raise ValueError(f"Production configuration errors: {'; '.join(errors)}")

        return self

    def check_optional_services(self) -> dict:
        """
        Check status of optional service configurations
        Returns dict with service status information
        """
        return {
            "claude_api": {
                "configured": bool(self.claude_api_key),
                "required_for": ["summarization", "action_extraction", "critique"],
            },
            "clova_stt": {
                "configured": bool(self.clova_api_key and self.clova_api_secret),
                "required_for": ["speech_to_text"],
            },
            "redis": {
                "configured": bool(self.redis_url),
                "required_for": ["caching", "rate_limiting", "session_storage"],
            },
            "minio": {
                "configured": bool(self.minio_access_key and self.minio_secret_key),
                "required_for": ["audio_file_storage"],
            },
            "slack": {
                "configured": bool(self.slack_webhook_url),
                "required_for": ["slack_notifications", "review_alerts"],
            },
            "google_calendar": {
                "configured": bool(self.google_calendar_credentials),
                "required_for": ["calendar_events", "meeting_scheduling"],
            },
            "notion": {
                "configured": bool(self.notion_api_key),
                "required_for": ["notion_pages", "meeting_documentation"],
            },
            "jira": {
                "configured": bool(self.jira_url and self.jira_email and self.jira_api_token),
                "required_for": ["jira_issues", "action_item_tracking"],
            },
        }

    def log_configuration_status(self):
        """Log the current configuration status"""
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Debug mode: {self.debug}")

        services = self.check_optional_services()
        for service, info in services.items():
            status = "✓ Configured" if info["configured"] else "✗ Not configured"
            logger.info(f"  {service}: {status}")
            if not info["configured"]:
                logger.warning(
                    f"    Features disabled: {', '.join(info['required_for'])}"
                )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def validate_settings_on_startup():
    """
    Validate settings when application starts
    Should be called during app initialization
    """
    try:
        settings = get_settings()
        settings.log_configuration_status()
        return settings
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise ConfigurationError(f"Failed to load configuration: {e}") from e


# Initialize settings (will raise on invalid config)
try:
    settings = get_settings()
except Exception as e:
    logger.error(f"Failed to load settings: {e}")
    # Re-raise to prevent app from starting with invalid config
    raise
