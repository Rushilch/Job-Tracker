"""Beanie ODM Document models for Interview Lab: Tags, Questions, Experiences, and Flash Cards."""

from datetime import datetime
from beanie import Document, Indexed
from pydantic import Field
import pymongo

from shared.schemas.interview_lab import (
    ExperienceResponse,
    FlashCardResponse,
    InterviewProcessStep,
    InterviewQA,
    QuestionResponse,
    ResourceLink,
    SolutionEntry,
    TagResponse,
)


class TagDocument(Document):
    """MongoDB Document for storing user-created taxonomy tags."""

    name: str = Field(..., description="Unique tag name")
    color: str = Field(default="#c25e2e")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interview_tags"
        indexes = [
            [("name", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]

    def to_response_dto(self) -> TagResponse:
        return TagResponse(
            id=str(self.id),
            name=self.name,
            color=self.color,
            created_at=self.created_at,
        )


class QuestionDocument(Document):
    """MongoDB Document for storing DSA / LeetCode questions and multi-solutions."""

    title: str
    description: str = ""
    difficulty: str = "Medium"
    topic: str = ""
    application_id: str | None = None
    company: str | None = None
    role: str | None = None
    solutions: list[SolutionEntry] = Field(default_factory=list)
    links: list[ResourceLink] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interview_questions"
        indexes = [
            [("title", pymongo.TEXT), ("topic", pymongo.TEXT), ("notes", pymongo.TEXT)],
            [("application_id", pymongo.ASCENDING)],
            [("company", pymongo.ASCENDING)],
            [("difficulty", pymongo.ASCENDING)],
            [("tags", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]

    def to_response_dto(self) -> QuestionResponse:
        return QuestionResponse(
            id=str(self.id),
            title=self.title,
            description=self.description,
            difficulty=self.difficulty,
            topic=self.topic,
            application_id=self.application_id,
            company=self.company,
            role=self.role,
            solutions=self.solutions,
            links=self.links,
            tags=self.tags,
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class ExperienceDocument(Document):
    """MongoDB Document for storing user interview experiences."""

    company: str
    role: str = "Software Engineer"
    application_id: str | None = None
    date: datetime | None = None
    interview_process: list[InterviewProcessStep] = Field(default_factory=list)
    questions_asked: list[InterviewQA] = Field(default_factory=list)
    rating: int = Field(default=5, ge=1, le=10)
    overall_notes: str = ""
    links: list[ResourceLink] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    outcome: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interview_experiences"
        indexes = [
            [("application_id", pymongo.ASCENDING)],
            [("company", pymongo.ASCENDING)],
            [("rating", pymongo.DESCENDING)],
            [("tags", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]

    def to_response_dto(self) -> ExperienceResponse:
        return ExperienceResponse(
            id=str(self.id),
            company=self.company,
            role=self.role,
            application_id=self.application_id,
            date=self.date,
            interview_process=self.interview_process,
            questions_asked=self.questions_asked,
            rating=self.rating,
            overall_notes=self.overall_notes,
            links=self.links,
            tags=self.tags,
            outcome=self.outcome,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class FlashCardDocument(Document):
    """MongoDB Document for storing manual revision flash cards."""

    front: str
    back: str
    application_id: str | None = None
    company: str | None = None
    tags: list[str] = Field(default_factory=list)
    links: list[ResourceLink] = Field(default_factory=list)
    difficulty: str = "Medium"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "interview_flashcards"
        indexes = [
            [("application_id", pymongo.ASCENDING)],
            [("company", pymongo.ASCENDING)],
            [("difficulty", pymongo.ASCENDING)],
            [("tags", pymongo.ASCENDING)],
            [("created_at", pymongo.DESCENDING)],
        ]

    def to_response_dto(self) -> FlashCardResponse:
        return FlashCardResponse(
            id=str(self.id),
            front=self.front,
            back=self.back,
            application_id=self.application_id,
            company=self.company,
            tags=self.tags,
            links=self.links,
            difficulty=self.difficulty,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
