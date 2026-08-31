"""Unit and integration tests for Job Application CRUD endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(app_client: AsyncClient):
    """Test health check endpoint."""
    res = await app_client.get("/api/applications/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy", "service": "application-service"}


@pytest.mark.asyncio
async def test_create_and_get_application(app_client: AsyncClient):
    """Test creating an application and retrieving it by ID."""
    payload = {
        "company": "Google",
        "role": "Software Engineer",
        "location": "Mountain View, CA",
        "salary_range": "$150k - $200k",
        "status": "applied",
        "tags": ["Full-time", "Backend"],
    }
    create_res = await app_client.post("/api/applications", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["company"] == "Google"
    assert created_data["role"] == "Software Engineer"
    assert created_data["status"] == "applied"
    assert "id" in created_data

    app_id = created_data["id"]
    get_res = await app_client.get(f"/api/applications/{app_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == app_id


@pytest.mark.asyncio
async def test_list_and_filter_applications(app_client: AsyncClient):
    """Test listing applications with status filter and search query."""
    await app_client.post(
        "/api/applications",
        json={"company": "Microsoft", "role": "Full Stack Dev", "status": "applied", "tags": ["c#"]},
    )
    await app_client.post(
        "/api/applications",
        json={"company": "Amazon", "role": "Backend Engineer", "status": "interview_scheduled"},
    )

    # Filter by status
    list_res = await app_client.get("/api/applications?status=applied")
    assert list_res.status_code == 200
    apps = list_res.json()
    assert len(apps) == 1
    assert apps[0]["company"] == "Microsoft"

    # Search query
    search_res = await app_client.get("/api/applications?search=Amazon")
    assert search_res.status_code == 200
    search_apps = search_res.json()
    assert len(search_apps) == 1
    assert search_apps[0]["company"] == "Amazon"


@pytest.mark.asyncio
async def test_update_status_and_timeline(app_client: AsyncClient):
    """Test updating application status and checking timeline logging."""
    create_res = await app_client.post(
        "/api/applications",
        json={"company": "Meta", "role": "ML Engineer", "status": "discovered"},
    )
    app_id = create_res.json()["id"]

    # Transition status
    update_res = await app_client.patch(
        f"/api/applications/{app_id}/status",
        json={"status": "interview_scheduled", "note": "Passed screen, tech round next week"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["status"] == "interview_scheduled"
    assert len(updated_data["timeline"]) >= 2
    assert updated_data["timeline"][-1]["event"] == "Status changed from discovered to interview_scheduled"


@pytest.mark.asyncio
async def test_delete_application(app_client: AsyncClient):
    """Test deleting an application."""
    create_res = await app_client.post(
        "/api/applications",
        json={"company": "Stripe", "role": "Backend Engineer", "status": "discovered"},
    )
    app_id = create_res.json()["id"]

    del_res = await app_client.delete(f"/api/applications/{app_id}")
    assert del_res.status_code == 204

    get_res = await app_client.get(f"/api/applications/{app_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_export_excel(app_client: AsyncClient):
    """Test exporting applications to an Excel XLSX workbook."""
    await app_client.post(
        "/api/applications",
        json={"company": "Netflix", "role": "Senior Distributed Systems Engineer", "status": "interview_scheduled"},
    )

    export_res = await app_client.get("/api/applications/export/excel")
    assert export_res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in export_res.headers["content-type"]
    assert len(export_res.content) > 1000


@pytest.mark.asyncio
async def test_upload_resume(app_client: AsyncClient):
    """Test uploading a resume file to an application."""
    create_res = await app_client.post(
        "/api/applications",
        json={"company": "Apple", "role": "Firmware / Software Engineer", "status": "applied"},
    )
    app_id = create_res.json()["id"]

    sample_resume_content = b"Experience: 3 years Python, FastAPI, Docker, C#, Angular, MongoDB."
    files = {"file": ("my_resume.txt", sample_resume_content, "text/plain")}

    upload_res = await app_client.post(f"/api/applications/{app_id}/resume/upload", files=files)
    assert upload_res.status_code == 200
    updated_data = upload_res.json()
    assert updated_data["resume_filename"] == "my_resume.txt"
    assert "Python, FastAPI" in updated_data["resume_text"]
    assert any("resume attached" in t["event"].lower() for t in updated_data["timeline"])
