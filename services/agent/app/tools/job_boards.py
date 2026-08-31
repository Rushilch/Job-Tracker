"""Client integrations for legitimate job board APIs (Adzuna, RemoteOK, Greenhouse)."""

import httpx
import structlog

logger = structlog.get_logger()


class AdzunaClient:
    """Client for Adzuna public job search API."""

    def __init__(self, app_id: str | None = None, app_key: str | None = None):
        self.app_id = app_id
        self.app_key = app_key
        self.base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"

    async def search_jobs(self, query: str, country: str = "us") -> list[dict]:
        """Search jobs by keywords/title via Adzuna API."""
        if not self.app_id or not self.app_key:
            logger.warning("adzuna_credentials_missing", message="Returning mock/empty listings")
            return []

        async with httpx.AsyncClient() as client:
            params = {
                "app_id": self.app_id,
                "app_key": self.app_key,
                "what": query,
                "content-type": "application/json",
            }
            res = await client.get(self.base_url, params=params, timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                return data.get("results", [])
            return []


class RemoteOKClient:
    """Client for RemoteOK API (public remote listings)."""

    def __init__(self):
        self.base_url = "https://remoteok.com/api"

    async def fetch_remote_jobs(self, tags: list[str] | None = None) -> list[dict]:
        """Fetch remote developer postings from RemoteOK."""
        headers = {"User-Agent": "JobSearchAutomationPlatform/1.0"}
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(self.base_url, headers=headers, timeout=10.0)
                if res.status_code == 200:
                    data = res.json()
                    # Filter out metadata item
                    return [item for item in data if isinstance(item, dict) and "position" in item]
            except Exception as e:
                logger.error("remoteok_fetch_failed", error=str(e))
        return []
