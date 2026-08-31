"""Pydantic schemas for Resume Personalization and Versioning."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ResumeBullet(BaseModel):
    """An individual achievement/experience bullet point."""

    text: str
    skills_highlighted: list[str] = Field(default_factory=list)
    relevance_score: float | None = None


class ResumeSection(BaseModel):
    """A section of a structured resume (e.g. Experience, Projects, Skills, Education)."""

    section_name: str
    items: list[dict[str, str | list[str] | list[ResumeBullet]]] = Field(default_factory=list)


class StructuredResume(BaseModel):
    """Full structured JSON representation of a resume."""

    name: str
    email: str
    phone: str | None = None
    links: dict[str, str] = Field(default_factory=dict, description="e.g. {'github': '...', 'linkedin': '...'}")
    summary: str | None = None
    skills: dict[str, list[str]] = Field(
        default_factory=dict,
        description="e.g. {'languages': ['Python', 'C#', 'Java'], 'frameworks': ['FastAPI', 'Angular']}",
    )
    experience: list[dict] = Field(default_factory=list)
    projects: list[dict] = Field(default_factory=list)
    education: list[dict] = Field(default_factory=list)


class ResumeVersionCreate(BaseModel):
    """Payload to create a new tailored resume version."""

    application_id: str
    json_content: StructuredResume
    tailored_notes: str | None = None


class ResumeVersionResponse(BaseModel):
    """Response model for a tailored resume version."""

    id: str
    application_id: str
    json_content: StructuredResume
    rendered_file_url: str | None = None
    tailored_notes: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
