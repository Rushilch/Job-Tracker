"""Configuration settings for Agent Service."""

from shared.config import CommonSettings


class AgentServiceSettings(CommonSettings):
    """Agent Service specific settings."""

    service_name: str = "agent-service"
    service_port: int = 8003

    # LLM Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    tavily_api_key: str | None = None
    default_model: str = "auto"

    # External APIs
    github_token: str | None = None
    adzuna_app_id: str | None = None
    adzuna_app_key: str | None = None


settings = AgentServiceSettings()
