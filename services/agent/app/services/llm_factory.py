"""LLM Provider Factory supporting Google Gemini 3.7 / 3.5, OpenAI, Anthropic, and local Heuristics."""

import os
from typing import Any
import structlog
from app.config import settings

logger = structlog.get_logger()


class LLMFactory:
    """Factory for initializing and selecting LangChain and Google GenAI LLM instances dynamically."""

    @staticmethod
    def get_configured_models() -> dict[str, Any]:
        """Return status of all supported LLM providers and currently active models."""
        gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        anthropic_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")

        models = [
            {
                "id": "gemini-3.7-flash",
                "name": "Google Gemini 3.7 Flash",
                "provider": "google",
                "configured": bool(gemini_key),
                "speed": "Ultra Fast",
                "tier": "Production",
            },
            {
                "id": "gemini-3.5-flash-lite",
                "name": "Google Gemini 3.5 Flash Lite",
                "provider": "google",
                "configured": bool(gemini_key),
                "speed": "Fastest",
                "tier": "High Throughput",
            },
            {
                "id": "gemini-3.1-pro-preview",
                "name": "Google Gemini 3.1 Pro",
                "provider": "google",
                "configured": bool(gemini_key),
                "speed": "Standard",
                "tier": "Advanced Reasoning",
            },
            {
                "id": "gpt-4o-mini",
                "name": "OpenAI GPT-4o Mini",
                "provider": "openai",
                "configured": bool(openai_key),
                "speed": "Fast",
                "tier": "Production",
            },
            {
                "id": "claude-3-5-haiku",
                "name": "Anthropic Claude 3.5 Haiku",
                "provider": "anthropic",
                "configured": bool(anthropic_key),
                "speed": "Fast",
                "tier": "Production",
            },
            {
                "id": "heuristic",
                "name": "Deterministic Heuristic / NLP Engine",
                "provider": "offline",
                "configured": True,
                "speed": "Instant",
                "tier": "Local Fallback",
            },
        ]

        active_default = "heuristic"
        if gemini_key:
            active_default = "gemini-3.7-flash"
        elif openai_key:
            active_default = "gpt-4o-mini"
        elif anthropic_key:
            active_default = "claude-3-5-haiku"

        return {
            "models": models,
            "active_default": active_default,
            "providers_status": {
                "google_gemini": bool(gemini_key),
                "openai": bool(openai_key),
                "anthropic": bool(anthropic_key),
                "offline_nlp": True,
            },
        }

    @staticmethod
    def get_llm(model_id: str | None = None, temperature: float = 0.2):
        """Instantiate selected LLM or appropriate fallback."""
        requested = model_id or "auto"

        gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        openai_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY")
        anthropic_key = settings.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")

        # Google Gemini Models (3.7 Flash, 3.6 Flash, 3.5 Flash Lite, 3.1 Pro, etc.)
        if requested in (
            "auto",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-pro-preview",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
        ) or requested.startswith("gemini"):
            if gemini_key:
                from langchain_google_genai import ChatGoogleGenerativeAI

                target_model = "gemini-3.7-flash"
                if "lite" in requested:
                    target_model = "gemini-3.5-flash-lite"
                elif "pro" in requested:
                    target_model = "gemini-3.1-pro-preview"
                elif "3.6" in requested:
                    target_model = "gemini-3.6-flash"

                try:
                    return ChatGoogleGenerativeAI(
                        model=target_model,
                        google_api_key=gemini_key,
                        temperature=temperature,
                    )
                except Exception as e:
                    logger.warning("gemini_init_failed", model=target_model, error=str(e))

        if requested in ("auto", "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo") or (requested.startswith("gemini") and not gemini_key):
            if openai_key:
                from langchain_openai import ChatOpenAI

                target_model = "gpt-4o-mini" if requested == "auto" else requested
                return ChatOpenAI(model=target_model, api_key=openai_key, temperature=temperature)

        if requested in ("auto", "claude-3-5-haiku", "claude-3-5-sonnet") or not (gemini_key or openai_key):
            if anthropic_key:
                from langchain_anthropic import ChatAnthropic

                return ChatAnthropic(
                    model="claude-3-5-haiku-20241022",
                    api_key=anthropic_key,
                    temperature=temperature,
                )

        # Returns None if using offline heuristics engine
        return None

    @staticmethod
    def update_api_keys(
        gemini_api_key: str | None = None,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        github_token: str | None = None,
    ):
        """Update runtime API keys in memory and environment."""
        if gemini_api_key is not None:
            settings.gemini_api_key = gemini_api_key.strip()
            os.environ["GEMINI_API_KEY"] = gemini_api_key.strip()
            os.environ["GOOGLE_API_KEY"] = gemini_api_key.strip()
        if openai_api_key is not None:
            settings.openai_api_key = openai_api_key.strip()
            os.environ["OPENAI_API_KEY"] = openai_api_key.strip()
        if anthropic_api_key is not None:
            settings.anthropic_api_key = anthropic_api_key.strip()
            os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key.strip()
        if github_token is not None:
            settings.github_token = github_token.strip()
            os.environ["GITHUB_TOKEN"] = github_token.strip()

        logger.info("api_keys_updated_in_runtime")

    @staticmethod
    async def test_connection(model_id: str) -> dict[str, Any]:
        """Send a test ping to the specified model and return latency and response."""
        import time
        from langchain_core.messages import HumanMessage

        if model_id == "heuristic":
            return {
                "status": "success",
                "model_id": "heuristic",
                "message": "Deterministic Heuristics / Offline NLP Engine is online and operational.",
                "latency_ms": 1,
            }

        # Handle Gemini test via google-genai or langchain
        if "gemini" in model_id:
            gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not gemini_key:
                return {
                    "status": "error",
                    "model_id": model_id,
                    "message": "Google Gemini API Key is missing. Add your key in AI Settings or .env.",
                    "latency_ms": 0,
                }

            start_time = time.time()
            # Try google.genai Client first, then LangChain
            target_model = "gemini-3.7-flash"
            if "lite" in model_id:
                target_model = "gemini-3.5-flash-lite"
            elif "pro" in model_id:
                target_model = "gemini-3.1-pro-preview"
            elif "3.6" in model_id:
                target_model = "gemini-3.6-flash"

            try:
                from google import genai

                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model=target_model,
                    contents="Reply with: 'Connected successfully to Gemini!'",
                )
                latency = int((time.time() - start_time) * 1000)
                reply_text = response.text or "Connected"
                return {
                    "status": "success",
                    "model_id": target_model,
                    "message": f"Successfully connected to {target_model}! Response: '{reply_text.strip()}'",
                    "latency_ms": latency,
                }
            except Exception as e_genai:
                logger.info("direct_genai_client_failed_trying_langchain", error=str(e_genai))
                try:
                    llm = LLMFactory.get_llm(target_model)
                    if llm:
                        res = await llm.ainvoke([HumanMessage(content="Reply with: 'Connected'")])
                        latency = int((time.time() - start_time) * 1000)
                        return {
                            "status": "success",
                            "model_id": target_model,
                            "message": f"Successfully connected to {target_model}! Response: '{res.content.strip()}'",
                            "latency_ms": latency,
                        }
                except Exception as e_lc:
                    pass

                latency = int((time.time() - start_time) * 1000)
                return {
                    "status": "error",
                    "model_id": target_model,
                    "message": f"Connection failed: {str(e_genai)}",
                    "latency_ms": latency,
                }

        llm = LLMFactory.get_llm(model_id)
        if not llm:
            return {
                "status": "error",
                "model_id": model_id,
                "message": f"API Key for {model_id} is missing or not configured. Add your key in AI Settings or .env.",
                "latency_ms": 0,
            }

        start_time = time.time()
        try:
            res = await llm.ainvoke([HumanMessage(content="Reply with exactly: 'Connected'")])
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "success",
                "model_id": model_id,
                "message": f"Successfully connected to {model_id}! Response: {res.content.strip()}",
                "latency_ms": latency,
            }
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            return {
                "status": "error",
                "model_id": model_id,
                "message": f"Connection failed: {str(e)}",
                "latency_ms": latency,
            }
