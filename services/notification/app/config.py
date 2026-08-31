"""Configuration settings for Notification Service."""

from shared.config import CommonSettings


class NotificationServiceSettings(CommonSettings):
    """Notification Service settings."""

    service_name: str = "notification-service"
    service_port: int = 8004

    auto_ghosting_days_threshold: int = 14
    nightly_digest_hour: int = 20


settings = NotificationServiceSettings()
