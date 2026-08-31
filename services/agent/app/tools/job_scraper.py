"""Web scraper and structured Job Description extractor using httpx & BeautifulSoup."""

from bs4 import BeautifulSoup
import httpx
import structlog

logger = structlog.get_logger()


class JobScraperService:
    """Scrapes public job listings and extracts structured metadata (Title, Company, JD)."""

    @staticmethod
    async def scrape_job_url(url: str) -> dict[str, str | None]:
        """Fetch and parse clean text and metadata from a job posting URL."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=12.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    logger.warning("job_scrape_failed", status_code=res.status_code, url=url)
                    return {
                        "url": url,
                        "title": None,
                        "company": None,
                        "location": None,
                        "jd_text": None,
                        "status": "error",
                        "message": f"HTTP {res.status_code} returned by host",
                    }

                html = res.text
                soup = BeautifulSoup(html, "html.parser")

                # Remove scripts, styles, and navigation noise
                for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                    tag.decompose()

                # Extract title
                title = None
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()

                # Try OpenGraph / Twitter meta tags
                og_title = soup.find("meta", property="og:title") or soup.find("meta", name="twitter:title")
                if og_title and og_title.get("content"):
                    title = og_title["content"].strip()

                og_company = soup.find("meta", property="og:site_name")
                company = og_company["content"].strip() if og_company and og_company.get("content") else None

                # Clean main text
                body_text = soup.get_text(separator="\n", strip=True)
                lines = [line.strip() for line in body_text.splitlines() if line.strip()]
                clean_jd = "\n".join(lines[:250])  # Cap at top 250 structured lines

                return {
                    "url": url,
                    "title": title,
                    "company": company,
                    "location": None,
                    "jd_text": clean_jd,
                    "status": "success",
                    "message": "Job description extracted successfully",
                }
        except Exception as e:
            logger.error("job_scrape_exception", error=str(e), url=url)
            return {
                "url": url,
                "title": None,
                "company": None,
                "location": None,
                "jd_text": None,
                "status": "error",
                "message": str(e),
            }
