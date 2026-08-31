"""Tests for Agent Service LLM Resume Tailoring, Model Discovery, Match Checker, and Scraping."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agent_health(agent_client: AsyncClient):
    """Test agent service health endpoint."""
    res = await agent_client.get("/api/agent/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agent-service"


@pytest.mark.asyncio
async def test_models_list(agent_client: AsyncClient):
    """Test getting available AI models including Gemini."""
    res = await agent_client.get("/api/agent/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    model_ids = [m["id"] for m in data["models"]]
    assert "gemini-3.7-flash" in model_ids
    assert "gemini-3.5-flash-lite" in model_ids
    assert "heuristic" in model_ids


@pytest.mark.asyncio
async def test_check_match(agent_client: AsyncClient):
    """Test JD and skills match checking."""
    payload = {
        "company": "Google",
        "role": "Cloud Software Engineer",
        "jd_text": "Requirements: Python, FastAPI, Docker, Distributed Systems, Kubernetes.",
        "skills_text": "Python, FastAPI, Docker, Asyncio, MongoDB, Git.",
        "model_id": "heuristic",
    }
    res = await agent_client.post("/api/agent/check-match", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "match_percentage" in data
    assert data["match_percentage"] >= 40.0
    assert "verdict" in data
    assert len(data["matched_skills"]) > 0
    assert len(data["talking_points"]) > 0


@pytest.mark.asyncio
async def test_upload_resume_for_match(agent_client: AsyncClient):
    """Test uploading resume file for ATS analysis against JD."""
    resume_content = b"Candidate Resume\nSkills: Python, FastAPI, Docker, PostgreSQL, Angular, Redis, Microservices\nExperience: Built scalable APIs."
    files = {"file": ("my_resume.txt", resume_content, "text/plain")}
    data = {
        "jd_text": "Requirements: Python, FastAPI, Docker, Kubernetes, PostgreSQL, Redis, REST APIs.",
        "company": "Stripe",
        "role": "Backend Engineer",
        "model_id": "heuristic",
    }
    res = await agent_client.post("/api/agent/upload-resume-for-match", data=data, files=files)
    assert res.status_code == 200
    res_data = res.json()
    assert "ats_score" in res_data or "match_percentage" in res_data
    assert "matched_skills" in res_data
    assert "necessary_changes" in res_data
    assert len(res_data["necessary_changes"]) > 0


@pytest.mark.asyncio
async def test_career_sites_endpoints(agent_client: AsyncClient):
    """Test adding and listing custom career sites."""
    # 1. Get career sites
    res = await agent_client.get("/api/agent/career-sites")
    assert res.status_code == 200
    sites = res.json()
    assert isinstance(sites, list)
    assert len(sites) > 0

    # 2. Add custom career site
    add_payload = {
        "company_name": "OpenAI",
        "site_type": "greenhouse",
        "identifier": "openai",
    }
    res_add = await agent_client.post("/api/agent/career-sites", json=add_payload)
    assert res_add.status_code == 200
    data_add = res_add.json()
    assert data_add["status"] == "success"
    assert data_add["site"]["name"] == "Openai"


@pytest.mark.asyncio
async def test_interview_prep(agent_client: AsyncClient):
    """Test interview and DSA questions research."""
    payload = {
        "company": "Amazon",
        "role": "Software Development Engineer II",
        "model_id": "heuristic",
    }
    res = await agent_client.post("/api/agent/interview-prep", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["company"] == "Amazon"
    assert len(data["dsa_questions"]) >= 2
    assert any(q["difficulty"] in ("Easy", "Medium", "Hard") for q in data["dsa_questions"])
    assert len(data["system_design_topics"]) > 0
    assert len(data["behavioral_questions"]) > 0


@pytest.mark.asyncio
async def test_discover_jobs(agent_client: AsyncClient):
    """Test live job discovery and feed scraping."""
    res = await agent_client.get("/api/agent/discover-jobs?query=Python&limit=5")
    assert res.status_code == 200
    jobs = res.json()
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    first_job = jobs[0]
    assert "role" in first_job
    assert "company" in first_job
    assert "relevance_score" in first_job


@pytest.mark.asyncio
async def test_resume_tailoring_direct(agent_client: AsyncClient):
    """Test LLM resume tailoring with candidate text and JD."""
    payload = {
        "company": "Bloomberg",
        "role": "Senior Software Engineer",
        "jd_text": "Requirements: Strong Python, FastAPI, Docker, and distributed systems design.",
        "resume_text": "Experience: Built backend APIs with Python, FastAPI, Docker, and Angular frontend.",
        "model_id": "heuristic",
    }
    res = await agent_client.post("/api/agent/tailor", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "relevance_score" in data
    assert data["relevance_score"] >= 40.0
    assert len(data["tailored_bullets"]) >= 3


@pytest.mark.asyncio
async def test_run_full_langgraph_pipeline(agent_client: AsyncClient):
    """Test invoking the real LangGraph multi-agent pipeline end-to-end."""
    profile_payload = {
        "target_roles": ["Software Engineer", "Backend Engineer"],
        "target_locations": ["Remote"],
        "min_salary": 120000,
        "max_experience_years": 3,
        "requires_visa_sponsorship": True,
        "graduation_date": "2026-05-15",
    }
    res = await agent_client.post("/api/agent/run-pipeline", json=profile_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "execution_log" in data
    assert len(data["execution_log"]) >= 4
    steps = [log["step"] for log in data["execution_log"]]
    assert "discovery" in steps
    assert "github_match" in steps
    assert "resume_tailoring" in steps
    assert "interview_prep" in steps


@pytest.mark.asyncio
async def test_update_runtime_keys(agent_client: AsyncClient):
    """Test updating API keys dynamically at runtime."""
    payload = {
        "gemini_api_key": "AIzaSyTestMockKey123",
        "github_token": "ghp_TestMockToken456",
    }
    res = await agent_client.post("/api/agent/settings/keys", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["models_status"]["providers_status"]["google_gemini"] is True


@pytest.mark.asyncio
async def test_diagnostics_ping(agent_client: AsyncClient):
    """Test connection diagnostics ping for heuristic engine."""
    res = await agent_client.post("/api/agent/test-connection", json={"model_id": "heuristic"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "heuristic" in data["model_id"]


@pytest.mark.asyncio
async def test_export_jobs_excel(agent_client: AsyncClient):
    """Test exporting discovered jobs to formatted Excel spreadsheet."""
    res = await agent_client.get("/api/agent/discover-jobs/export/excel?query=Python&location=Remote&limit=5")
    assert res.status_code == 200
    assert "spreadsheetml" in res.headers.get("content-type", "")
    assert len(res.content) > 1000  # valid binary xlsx content


@pytest.mark.asyncio
async def test_interview_prep_resources_and_reddit(agent_client: AsyncClient):
    """Test that interview prep kit contains LeetCode links and Reddit debriefs."""
    payload = {
        "company": "Google",
        "role": "Software Engineer",
        "use_ai": False,
    }
    res = await agent_client.post("/api/agent/interview-prep", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "dsa_questions" in data
    assert len(data["dsa_questions"]) > 0
    first_q = data["dsa_questions"][0]
    assert "leetcode_url" in first_q or "hint" in first_q
    assert "reddit_experiences" in data
    assert len(data["reddit_experiences"]) > 0
