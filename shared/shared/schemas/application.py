"""Pydantic schemas for Job Applications and Application Tracking."""

from datetime import datetime
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ApplicationStatus(str, Enum):
    """Lifecycle status stages for job applications."""

    DISCOVERED = "discovered"
    APPLIED = "applied"
    RESPONDED = "responded"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"


class TimelineEntry(BaseModel):
    """An event in the history/timeline of an application."""

    date: datetime = Field(default_factory=datetime.utcnow)
    event: str = Field(..., description="E.g., 'Status changed to Applied', 'Recruiter Screen call'")
    notes: str | None = Field(default=None, description="Optional detailed notes for the event")


class ApplicationBase(BaseModel):
    """Base fields for an application."""

    company: str = Field(..., min_length=1, max_length=150, description="Company name")
    role: str = Field(..., min_length=1, max_length=150, description="Job title / role")
    job_url: str | None = Field(default=None, description="URL to the job listing")
    location: str | None = Field(default=None, description="Job location or 'Remote'")
    salary_range: str | None = Field(default=None, description="Salary or compensation range")
    jd_snapshot: str | None = Field(default=None, description="Full text or snapshot of JD")
    status: ApplicationStatus = Field(default=ApplicationStatus.DISCOVERED)
    relevance_score: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Relevance score (0-100) assigned by AI"
    )
    notes: str | None = Field(default=None, description="General user notes")
    tags: list[str] = Field(default_factory=list, description="Custom tags, e.g. 'referral', 'urgent'")
    
    # Resume & Tailoring metadata
    resume_filename: str | None = Field(default=None, description="Uploaded resume filename")
    resume_text: str | None = Field(default=None, description="Extracted resume text content")
    tailored_resume_summary: str | None = Field(default=None, description="AI generated executive summary tailored for JD")
    tailored_bullets: list[str] = Field(default_factory=list, description="AI tailored bullet points emphasizing matching keywords")
    matched_skills: list[str] = Field(default_factory=list, description="Candidate skills directly matching JD requirements")
    missing_skills: list[str] = Field(default_factory=list, description="JD required skills to review/prep for")


class ApplicationCreate(ApplicationBase):
    """Payload to create a new application."""

    resume_version_id: str | None = None
    prep_doc_id: str | None = None


class ApplicationUpdate(BaseModel):
    """Payload to update an existing application (all fields optional)."""

    company: str | None = None
    role: str | None = None
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    jd_snapshot: str | None = None
    status: ApplicationStatus | None = None
    relevance_score: float | None = None
    notes: str | None = None
    tags: list[str] | None = None
    resume_filename: str | None = None
    resume_text: str | None = None
    tailored_resume_summary: str | None = None
    tailored_bullets: list[str] | None = None
    matched_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    resume_version_id: str | None = None
    prep_doc_id: str | None = None
    interview_date: datetime | None = None


class ApplicationStatusUpdate(BaseModel):
    """Payload to update only the status and optional note for timeline."""

    status: ApplicationStatus
    note: str | None = None


class ApplicationResponse(ApplicationBase):
    """Response model for job application details."""

    id: str = Field(..., description="Unique application ID (MongoDB ObjectId as string)")
    date_discovered: datetime = Field(default_factory=datetime.utcnow)
    date_applied: datetime | None = None
    interview_date: datetime | None = None
    resume_version_id: str | None = None
    prep_doc_id: str | None = None
    timeline: list[TimelineEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ApplicationFilter(BaseModel):
    """Query parameters for filtering applications."""

    status: ApplicationStatus | None = None
    company: str | None = None
    tag: str | None = None
    search: str | None = None
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
