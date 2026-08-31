"""FastAPI entrypoint for Agent Service.

Provides agent endpoints for:
- Model selection & Gemini/OpenAI/Anthropic discovery
- Web scraping & structured Job Description ingestion
- Direct JD & Skills Match Checker + Resume File Upload ATS Analysis
- Add and List Custom Company Career Sites (Greenhouse / Lever)
- DSA & Technical Interview Question Research (LeetCode/NeetCode + Reddit debriefs)
- Live Developer Job Postings Scraping across Career Pages, Indeed, RemoteOK, Remotive, WWR
- Export Discovered Jobs to Excel (.xlsx)
- Resume Personalization & LangGraph State Workflows
"""

from typing import Any
from fastapi import APIRouter, FastAPI, File, Form, HTTPException, Query, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
from shared.logging import setup_logging
from shared.schemas.profile import EligibilityProfile
from app.config import settings
from app.graph.workflow import job_search_graph
from app.services.job_discovery_service import JobDiscoveryService
from app.services.llm_factory import LLMFactory
from app.services.match_checker_service import MatchCheckerService
from app.services.tailoring_service import ResumeTailoringService
from app.tools.job_scraper import JobScraperService

logger = setup_logging(service_name=settings.service_name, log_level=settings.log_level)

app = FastAPI(
    title="Agent Service (Gemini, LangGraph & Job Scrapers)",
    description="Developer Job Search Automation, Resume Tailoring, DSA Research & Scraping.",
    version="0.3.0",
    docs_url="/api/agent/docs",
    openapi_url="/api/agent/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/agent", tags=["Agents"])


# Request / Response Schemas
class ScrapeJobRequest(BaseModel):
    url: str = Field(..., description="Target job listing URL")


class MatchCheckRequest(BaseModel):
    jd_text: str = Field(..., description="Pasted Job Description text")
    skills_text: str = Field(..., description="Candidate skills or resume text")
    company: str | None = None
    role: str | None = None
    model_id: str | None = Field(default="auto", description="Model identifier to use")


class AddCareerSiteRequest(BaseModel):
    company_name: str = Field(..., description="Company name, e.g. OpenAI, Uber, Cloudflare")
    site_type: str = Field(default="greenhouse", description="Career portal type: greenhouse or lever")
    identifier: str | None = Field(default=None, description="Company slug if different from name")


class TailorResumeRequest(BaseModel):
    company: str
    role: str
    jd_text: str | None = None
    resume_text: str | None = None
    model_id: str | None = "auto"


class TrackJobRequest(BaseModel):
    company: str
    role: str
    location: str | None = "Remote"
    salary_range: str | None = None
    job_url: str | None = None
    jd_snapshot: str | None = None
    tags: list[str] = Field(default_factory=list)
    relevance_score: float | None = None


class UpdateKeysRequest(BaseModel):
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    github_token: str | None = None


class TestConnectionRequest(BaseModel):
    model_id: str = Field(default="gemini-3.7-flash", description="Model ID to test")


# Endpoints
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check for Agent Service."""
    return {
        "status": "healthy",
        "service": settings.service_name,
        "models_available": LLMFactory.get_configured_models()["providers_status"],
    }


@router.get("/models")
async def get_available_models():
    """List supported AI models and check which LLM API keys are active."""
    return LLMFactory.get_configured_models()


@router.post("/settings/keys")
async def update_runtime_keys(payload: UpdateKeysRequest):
    """Update API keys dynamically in runtime."""
    LLMFactory.update_api_keys(
        gemini_api_key=payload.gemini_api_key,
        openai_api_key=payload.openai_api_key,
        anthropic_api_key=payload.anthropic_api_key,
        github_token=payload.github_token,
    )
    return {
        "status": "success",
        "message": "API keys updated successfully.",
        "models_status": LLMFactory.get_configured_models(),
    }


@router.post("/test-connection")
async def test_model_connection(payload: TestConnectionRequest):
    """Test live connectivity and latency for a chosen AI model."""
    logger.info("testing_model_connection", model_id=payload.model_id)
    return await LLMFactory.test_connection(payload.model_id)


@router.post("/check-match")
async def check_jd_and_skills_match(payload: MatchCheckRequest) -> dict[str, Any]:
    """Analyze pasted Job Description against candidate skills and output ATS analysis."""
    logger.info("checking_jd_skills_match", company=payload.company, role=payload.role)
    return await MatchCheckerService.analyze_match(
        jd_text=payload.jd_text,
        skills_text=payload.skills_text,
        company=payload.company,
        role=payload.role,
        model_id=payload.model_id,
    )


@router.post("/upload-resume-for-match")
async def upload_resume_and_check_match(
    file: UploadFile = File(...),
    jd_text: str = Form(...),
    company: str | None = Form(None),
    role: str | None = Form(None),
    model_id: str | None = Form("auto"),
) -> dict[str, Any]:
    """Upload candidate resume (PDF / TXT), extract text, and run deep ATS & role alignment analysis against JD."""
    logger.info("uploading_resume_for_ats_match", filename=file.filename, company=company)
    file_bytes = await file.read()
    extracted_resume_text = MatchCheckerService.extract_text_from_file(file_bytes, file.filename or "resume.pdf")

    if not extracted_resume_text:
        raise HTTPException(status_code=400, detail="Could not extract readable text from the uploaded resume.")

    result = await MatchCheckerService.analyze_match(
        jd_text=jd_text,
        skills_text=extracted_resume_text,
        company=company,
        role=role,
        model_id=model_id,
    )
    result["extracted_resume_preview"] = extracted_resume_text[:600]
    result["filename"] = file.filename
    return result


@router.get("/career-sites")
async def get_career_sites():
    """List all supported and user-added company career sites."""
    return JobDiscoveryService.get_custom_career_sites()


@router.post("/career-sites")
async def add_custom_career_site(payload: AddCareerSiteRequest):
    """Add a new company career portal (Greenhouse or Lever) to the live job discovery scraper."""
    logger.info("adding_custom_career_site", company=payload.company_name, site_type=payload.site_type)
    added = JobDiscoveryService.add_custom_career_site(
        company_name=payload.company_name,
        site_type=payload.site_type,
        identifier=payload.identifier or payload.company_name,
    )
    return {
        "status": "success",
        "message": f"Added {added['name']} ({added['type']}) to career scraping engine.",
        "site": added,
        "all_sites": JobDiscoveryService.get_custom_career_sites(),
    }


@router.get("/discover-jobs")
async def discover_live_jobs(
    query: str = Query(default="Software Engineer"),
    location: str = Query(default="Remote"),
    limit: int = Query(default=30, ge=1, le=200),
    page: int = Query(default=1, ge=1),
    offset: int = Query(default=0, ge=0),
    source_filter: str = Query(default="all"),
) -> list[dict[str, Any]]:
    """Scrape and aggregate live developer job postings across Career Pages, JobSpy, RemoteOK, Remotive, WWR."""
    logger.info("discovering_live_jobs", query=query, location=location, source=source_filter, page=page, offset=offset, limit=limit)
    return await JobDiscoveryService.discover_jobs(
        query=query,
        location=location,
        limit=limit,
        page=page,
        offset=offset,
        source_filter=source_filter,
    )


@router.get("/discover-jobs/export/excel")
async def export_discovered_jobs_excel(
    query: str = Query(default="Software Engineer"),
    location: str = Query(default="Remote"),
    limit: int = Query(default=40, ge=1, le=100),
    source_filter: str = Query(default="all"),
):
    """Export live scraped developer jobs to a styled Excel (.xlsx) spreadsheet."""
    logger.info("exporting_discovered_jobs_excel", query=query, location=location)
    jobs = await JobDiscoveryService.discover_jobs(
        query=query,
        location=location,
        limit=limit,
        source_filter=source_filter,
    )
    excel_bytes = JobDiscoveryService.export_jobs_to_excel(jobs)
    clean_filename = f"careerpilot_jobs_{query.replace(' ', '_').lower()}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={clean_filename}"},
    )


@router.post("/track-discovered-job")
async def track_discovered_job(payload: TrackJobRequest):
    """1-Click import a discovered job into the Application Tracker (MongoDB)."""
    app_svc_url = f"{settings.application_service_url}/api/applications"
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(
            app_svc_url,
            json={
                "company": payload.company,
                "role": payload.role,
                "location": payload.location,
                "salary_range": payload.salary_range,
                "job_url": payload.job_url,
                "jd_snapshot": payload.jd_snapshot,
                "status": "discovered",
                "tags": payload.tags or ["Discovered Feed"],
                "relevance_score": payload.relevance_score,
            },
        )
        if res.status_code not in (200, 201):
            raise HTTPException(status_code=res.status_code, detail="Failed to import to application service")
        return res.json()


@router.post("/scrape-job")
async def scrape_job_listing(payload: ScrapeJobRequest):
    """Scrape and extract structured Job Title, Company, and Clean JD text from any job URL."""
    logger.info("scraping_job_url", url=payload.url)
    return await JobScraperService.scrape_job_url(payload.url)


@router.post("/tailor")
async def tailor_resume_direct(payload: TailorResumeRequest) -> dict[str, Any]:
    """Run resume tailoring with provided JD and resume text."""
    logger.info("tailoring_resume_direct", company=payload.company, role=payload.role)
    return await ResumeTailoringService.tailor_resume(
        company=payload.company,
        role=payload.role,
        jd_text=payload.jd_text,
        resume_text=payload.resume_text,
        model_id=payload.model_id,
    )


@router.post("/tailor-application/{app_id}")
async def tailor_application_endpoint(app_id: str) -> dict[str, Any]:
    """Fetch application details from Application Service, tailor resume against JD, and persist results."""
    logger.info("tailoring_application", app_id=app_id)
    app_svc_url = f"{settings.application_service_url}/api/applications/{app_id}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(app_svc_url)
            if res.status_code != 200:
                raise HTTPException(status_code=res.status_code, detail=f"Could not load application {app_id}")
            app_data = res.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to connect to Application Service: {str(e)}")

    tailored = await ResumeTailoringService.tailor_resume(
        company=app_data.get("company", "Target Company"),
        role=app_data.get("role", "Software Engineer"),
        jd_text=app_data.get("jd_snapshot"),
        resume_text=app_data.get("resume_text"),
    )

    update_payload = {
        "tailored_resume_summary": tailored.get("tailored_summary"),
        "tailored_bullets": tailored.get("tailored_bullets", []),
        "matched_skills": tailored.get("matched_skills", []),
        "missing_skills": tailored.get("missing_skills", []),
        "relevance_score": tailored.get("relevance_score"),
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.put(app_svc_url, json=update_payload)
            await client.post(
                f"{settings.application_service_url}/api/applications/{app_id}/timeline",
                json={
                    "event": f"AI Resume Tailored ({tailored.get('relevance_score', 0):.0f}% Match)",
                    "notes": f"Matched skills: {', '.join(tailored.get('matched_skills', []))}",
                },
            )
        except Exception as e:
            logger.warning("failed_to_persist_tailored_results", error=str(e))

    return tailored


@router.post("/run-pipeline")
async def run_full_pipeline(profile: EligibilityProfile) -> dict[str, Any]:
    """Execute the end-to-end LangGraph job search workflow."""
    logger.info("invoking_langgraph_pipeline", target_roles=profile.target_roles)
    initial_state = {
        "eligibility_profile": profile.model_dump(),
        "raw_listings": [],
        "filtered_jobs": [],
        "selected_job": None,
        "base_resume": None,
        "tailored_resume": None,
        "prep_doc": None,
        "matched_projects": [],
        "errors": [],
        "execution_log": [],
    }
    final_state = await job_search_graph.ainvoke(initial_state)
    return {
        "status": "success",
        "execution_log": final_state.get("execution_log", []),
        "jobs_count": len(final_state.get("filtered_jobs", [])),
    }


app.include_router(router)


@app.get("/health", tags=["Health"])
async def root_health():
    return {"status": "healthy", "service": settings.service_name}
