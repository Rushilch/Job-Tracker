"""Module 1: Real Job Discovery and Scoring Agent Node.

Discovers live postings via RemoteOK API and WeWorkRemotely feeds,
scores against the user's Eligibility Profile, and pushes top matches to the Application Tracker.
"""

from typing import Any
import httpx
import structlog
from app.config import settings
from app.graph.state import JobSearchState
from app.services.job_discovery_service import JobDiscoveryService

logger = structlog.get_logger()


async def discover_and_score_jobs_node(state: JobSearchState) -> dict[str, Any]:
    """LangGraph node: fetches live listings and filters against candidate profile."""
    profile = state.get("eligibility_profile", {})
    target_roles = profile.get("target_roles", ["Software Engineer", "Backend Engineer"])
    locations = profile.get("target_locations", ["Remote"])
    primary_location = locations[0] if locations else "Remote"

    logger.info("executing_live_job_discovery", target_roles=target_roles, location=primary_location)

    all_discovered = []
    for role in target_roles[:2]:
        jobs = await JobDiscoveryService.discover_jobs(query=role, location=primary_location, limit=8)
        all_discovered.extend(jobs)

    # Deduplicate by role + company
    seen = set()
    unique_jobs = []
    for j in all_discovered:
        key = (j.get("company", "").lower(), j.get("role", "").lower())
        if key not in seen and j.get("company"):
            seen.add(key)
            unique_jobs.append(j)

    # Select highest match job as primary target for downstream nodes
    selected_job = state.get("selected_job")
    if not selected_job and unique_jobs:
        selected_job = unique_jobs[0]

    # Attempt to persist top matches into Application Service tracker
    persisted_count = 0
    app_svc_url = f"{settings.application_service_url}/api/applications"
    for job in unique_jobs[:5]:
        try:
            async with httpx.AsyncClient(timeout=0.5) as client:
                res = await client.post(
                    app_svc_url,
                    json={
                        "company": job.get("company"),
                        "role": job.get("role"),
                        "location": job.get("location", "Remote"),
                        "salary_range": job.get("salary_range"),
                        "job_url": job.get("job_url"),
                        "jd_snapshot": job.get("jd_snapshot"),
                        "status": "discovered",
                        "tags": ["LangGraph Discovery"] + (job.get("tags") or [])[:2],
                        "relevance_score": job.get("relevance_score", 85.0),
                    },
                )
                if res.status_code in (200, 201):
                    persisted_count += 1
        except Exception as e:
            logger.debug("could_not_persist_discovered_job", company=job.get("company"), error=str(e))

    return {
        "raw_listings": all_discovered,
        "filtered_jobs": unique_jobs,
        "selected_job": selected_job,
        "execution_log": state.get("execution_log", []) + [
            {
                "step": "discovery",
                "status": "completed",
                "message": f"Discovered {len(unique_jobs)} live job postings matching {', '.join(target_roles[:2])}. Persisted {persisted_count} to tracker.",
            }
        ],
    }
