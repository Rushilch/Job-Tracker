"""Shared configuration settings using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Base settings inherited across all backend services."""

    environment: str = "development"
    log_level: str = "INFO"
    mongodb_uri: str = "mongodb://localhost:27017/job_search"
    mongodb_db_name: str = "job_search"

    # Inter-service URLs
    application_service_url: str = "http://localhost:8001"
    auth_service_url: str = "http://localhost:8002"
    agent_service_url: str = "http://localhost:8003"
    notification_service_url: str = "http://localhost:8004"

    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
