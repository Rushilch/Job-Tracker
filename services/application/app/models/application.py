"""Beanie ODM Document model for Job Applications."""

from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field
import pymongo

from shared.schemas.application import (
    ApplicationResponse,
    ApplicationStatus,
    TimelineEntry,
)


class ApplicationDocument(Document):
    """MongoDB Document for storing Job Applications."""

    company: str
    role: str
    job_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    jd_snapshot: str | None = None
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    relevance_score: float | None = None
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Resume & Tailoring
    resume_filename: str | None = None
    resume_text: str | None = None
    tailored_resume_summary: str | None = None
    tailored_bullets: list[str] = Field(default_factory=list)
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    date_discovered: datetime = Field(default_factory=datetime.utcnow)
    date_applied: datetime | None = None
    interview_date: datetime | None = None

    resume_version_id: str | None = None
    prep_doc_id: str | None = None

    timeline: list[TimelineEntry] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "applications"
        indexes = [
            [
                ("company", pymongo.ASCENDING),
                ("role", pymongo.ASCENDING),
            ],
            [
                ("status", pymongo.ASCENDING),
                ("date_applied", pymongo.DESCENDING),
            ],
            [
                ("created_at", pymongo.DESCENDING),
            ],
        ]

    def to_response_dto(self) -> ApplicationResponse:
        """Convert Beanie Document to API Response DTO."""
        return ApplicationResponse(
            id=str(self.id),
            company=self.company,
            role=self.role,
            job_url=self.job_url,
            location=self.location,
            salary_range=self.salary_range,
            jd_snapshot=self.jd_snapshot,
            status=self.status,
            relevance_score=self.relevance_score,
            notes=self.notes,
            tags=self.tags,
            resume_filename=self.resume_filename,
            resume_text=self.resume_text,
            tailored_resume_summary=self.tailored_resume_summary,
            tailored_bullets=self.tailored_bullets,
            matched_skills=self.matched_skills,
            missing_skills=self.missing_skills,
            date_discovered=self.date_discovered,
            date_applied=self.date_applied,
            interview_date=self.interview_date,
            resume_version_id=self.resume_version_id,
            prep_doc_id=self.prep_doc_id,
            timeline=self.timeline,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
