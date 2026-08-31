"""REST API Endpoints for Job Applications."""

from typing import Annotated
from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from shared.schemas.application import (
    ApplicationCreate,
    ApplicationFilter,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    TimelineEntry,
)
from app.services.application_service import ApplicationService
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/applications", tags=["Applications"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Health check endpoint for Traefik and Docker health checks."""
    return {"status": "healthy", "service": "application-service"}


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_application_stats() -> dict:
    """Get aggregated application metrics and counts by status."""
    return await ApplicationService.get_stats()


@router.get("/export/excel")
async def export_applications_excel():
    """Export all job applications to a styled Microsoft Excel spreadsheet (.xlsx)."""
    excel_stream = await ExportService.export_applications_to_excel()
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=careerpilot_applications.xlsx"
        },
    )


@router.post("/{app_id}/resume/upload", response_model=ApplicationResponse)
async def upload_application_resume(app_id: str, file: UploadFile = File(...)) -> ApplicationResponse:
    """Upload a resume file (PDF, TXT, DOCX, JSON) to attach to a job application."""
    content = await file.read()
    updated = await ApplicationService.upload_resume(app_id, content, file.filename or "resume.pdf")
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{app_id}' not found",
        )
    return updated


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    status_filter: Annotated[ApplicationStatus | None, Query(alias="status")] = None,
    company: Annotated[str | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(description="Search company, role or location")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ApplicationResponse]:
    """List applications with optional filters and pagination."""
    filter_params = ApplicationFilter(
        status=status_filter,
        company=company,
        tag=tag,
        search=search,
        limit=limit,
        offset=offset,
    )
    return await ApplicationService.list_applications(filter_params)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationCreate) -> ApplicationResponse:
    """Create a new job application."""
    return await ApplicationService.create_application(payload)


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(app_id: str) -> ApplicationResponse:
    """Get single application details by ID."""
    app = await ApplicationService.get_by_id(app_id)
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{app_id}' not found",
        )
    return app


@router.put("/{app_id}", response_model=ApplicationResponse)
async def update_application(app_id: str, payload: ApplicationUpdate) -> ApplicationResponse:
    """Update fields on an application."""
    updated = await ApplicationService.update_application(app_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{app_id}' not found",
        )
    return updated


@router.patch("/{app_id}/status", response_model=ApplicationResponse)
async def update_application_status(app_id: str, payload: ApplicationStatusUpdate) -> ApplicationResponse:
    """Update only the application status (used for Kanban drag & drop)."""
    updated = await ApplicationService.update_status(app_id, payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{app_id}' not found",
        )
    return updated


@router.post("/{app_id}/timeline", response_model=ApplicationResponse)
async def add_timeline_entry(app_id: str, entry: TimelineEntry) -> ApplicationResponse:
    """Append a timeline entry to an application history."""
    updated = await ApplicationService.add_timeline_event(app_id, entry)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{app_id}' not found",
        )
    return updated


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(app_id: str) -> None:
    """Delete an application."""
    deleted = await ApplicationService.delete_application(app_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{app_id}' not found",
        )
