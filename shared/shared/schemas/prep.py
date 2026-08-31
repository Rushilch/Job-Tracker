"""Pydantic schemas for Interview and DSA Research Prep Docs."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SourcedItem(BaseModel):
    """An interview question or insight linked to its source or role archetype."""

    topic: str
    description: str
    difficulty: str | None = Field(default=None, description="'Easy', 'Medium', 'Hard', or 'N/A'")
    source_type: str = Field(
        default="general_pattern",
        description="'found_in_research' (Glassdoor/LeetCode/blogs) vs 'general_pattern'",
    )
    source_url: str | None = None


class QuestionCategory(BaseModel):
    """Group of interview questions (e.g., 'System Design', 'Algorithms', 'Behavioral')."""

    category_name: str
    questions: list[SourcedItem] = Field(default_factory=list)


class PrepDocCreate(BaseModel):
    """Payload to create an interview prep document for a company/role."""

    application_id: str
    company: str
    role: str
    question_categories: list[QuestionCategory] = Field(default_factory=list)
    dsa_topics: list[str] = Field(default_factory=list, description="Prioritized DSA topics, e.g. ['Trees', 'Graphs']")
    behavioral_themes: list[str] = Field(default_factory=list, description="Company values / leadership principles")
    prioritized_must_review: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class PrepDocResponse(BaseModel):
    """Response model for a company/role interview prep doc."""

    id: str
    application_id: str
    company: str
    role: str
    question_categories: list[QuestionCategory] = Field(default_factory=list)
    dsa_topics: list[str] = Field(default_factory=list)
    behavioral_themes: list[str] = Field(default_factory=list)
    prioritized_must_review: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
