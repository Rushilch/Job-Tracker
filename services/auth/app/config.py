"""Auth Service configuration."""

from shared.config import CommonSettings


class AuthServiceSettings(CommonSettings):
    """Auth Service specific settings."""

    service_name: str = "auth-service"
    service_port: int = 8002

    jwt_secret_key: str = "default-dev-secret-change-in-production-min-32-chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60


settings = AuthServiceSettings()
