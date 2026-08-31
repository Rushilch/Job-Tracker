"""Configuration settings for Application Service."""

from shared.config import CommonSettings


class ApplicationServiceSettings(CommonSettings):
    """Application Service specific settings."""

    service_name: str = "application-service"
    service_port: int = 8001


settings = ApplicationServiceSettings()
