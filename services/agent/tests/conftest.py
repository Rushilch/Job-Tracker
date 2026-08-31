"""Pytest configuration for Agent Service."""

import importlib.util
from pathlib import Path
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

agent_main_path = Path(__file__).parent.parent / "app" / "main.py"
spec = importlib.util.spec_from_file_location("agent_app_module", agent_main_path)
agent_app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_app_module)
agent_fastapi_app = agent_app_module.app


@pytest_asyncio.fixture
async def agent_client():
    """Create test client against Agent Service."""
    transport = ASGITransport(app=agent_fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
