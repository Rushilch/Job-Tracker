"""Pydantic v2 schemas for Interview Lab: Questions, Solutions, Experiences, and Flash Cards."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# --- Custom Tags ---
class TagBase(BaseModel):
    """User-defined taxonomy tag for categorizing items."""

    name: str = Field(..., description="Tag name, e.g. 'Dynamic Programming', 'Google'")
    color: str = Field(default="#c25e2e", description="Hex color for badge display")


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagResponse(TagBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# --- Resource Links ---
class ResourceLink(BaseModel):
    """Reusable external link attachment."""

    label: str = Field(..., description="Display text, e.g. 'LeetCode Problem', 'GitHub Repo'")
    url: str = Field(..., description="Target URL")


# --- DSA / LeetCode Questions ---
class SolutionEntry(BaseModel):
    """A specific solution approach to a coding problem."""

    label: str = Field(default="Solution 1", description="e.g. 'Brute Force', 'Optimal Hash Map'")
    code: str = Field(default="", description="Code snippet")
    language: str = Field(default="python", description="Language, e.g. 'python', 'cpp', 'java', 'typescript'")
    explanation: str = Field(default="", description="Explanation of intuition and approach")
    time_complexity: str = Field(default="", description="e.g. 'O(N)'")
    space_complexity: str = Field(default="", description="e.g. 'O(1)'")
    tags: list[str] = Field(default_factory=list, description="Tag names or IDs")


class QuestionBase(BaseModel):
    title: str = Field(..., description="Problem title, e.g. 'Two Sum'")
    description: str = Field(default="", description="Problem statement or notes")
    difficulty: str = Field(default="Medium", description="'Easy', 'Medium', or 'Hard'")
    topic: str = Field(default="", description="Primary topic e.g. 'Arrays & Hashing'")
    application_id: str | None = Field(default=None, description="Optional linked job application ID")
    company: str | None = Field(default=None, description="Optional company name e.g. 'Google'")
    role: str | None = Field(default=None, description="Optional role e.g. 'Software Engineer'")
    solutions: list[SolutionEntry] = Field(default_factory=list)
    links: list[ResourceLink] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    notes: str = Field(default="", description="Free-form markdown notes")


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: str | None = None
    topic: str | None = None
    application_id: str | None = None
    company: str | None = None
    role: str | None = None
    solutions: list[SolutionEntry] | None = None
    links: list[ResourceLink] | None = None
    tags: list[str] | None = None
    notes: str | None = None


class QuestionResponse(QuestionBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# --- Interview Experiences ---
class InterviewQA(BaseModel):
    """A specific question asked during an interview round and user's answer."""

    question: str = Field(..., description="The interview question")
    answer: str = Field(default="", description="The candidate's response or optimal answer")
    category: str = Field(default="Technical", description="e.g. 'Technical', 'Behavioral', 'System Design'")
    links: list[ResourceLink] = Field(default_factory=list)


class InterviewProcessStep(BaseModel):
    """A step/round in the interview pipeline."""

    round_number: int = Field(default=1, description="Round order index")
    round_type: str = Field(default="OA", description="'OA', 'TA', 'BA', 'SD', 'HR', 'HM', or custom")
    description: str = Field(default="", description="Details, e.g. 'Hackerrank 2 LC Medium'")


class ExperienceBase(BaseModel):
    company: str = Field(..., description="Company name, e.g. 'Google'")
    role: str = Field(default="Software Engineer", description="Target role")
    application_id: str | None = Field(default=None, description="Optional linked job application ID")
    date: datetime | None = Field(default=None, description="Interview date")
    interview_process: list[InterviewProcessStep] = Field(default_factory=list)
    questions_asked: list[InterviewQA] = Field(default_factory=list)
    rating: int = Field(default=5, ge=1, le=10, description="Self-evaluation rating on 1-10 scale")
    overall_notes: str = Field(default="", description="Overall takeaways, recruiter notes, etc.")
    links: list[ResourceLink] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    outcome: str = Field(default="", description="'Offer', 'Rejected', 'Pending', etc.")


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: str | None = None
    role: str | None = None
    application_id: str | None = None
    date: datetime | None = None
    interview_process: list[InterviewProcessStep] | None = None
    questions_asked: list[InterviewQA] | None = None
    rating: int | None = Field(default=None, ge=1, le=10)
    overall_notes: str | None = None
    links: list[ResourceLink] | None = None
    tags: list[str] | None = None
    outcome: str | None = None


class ExperienceResponse(ExperienceBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


# --- Flash Cards ---
class FlashCardBase(BaseModel):
    front: str = Field(..., description="Prompt or question on the front of card")
    back: str = Field(..., description="Answer or explanation on the back of card")
    application_id: str | None = Field(default=None, description="Optional linked job application ID")
    company: str | None = Field(default=None, description="Optional company name")
    tags: list[str] = Field(default_factory=list)
    links: list[ResourceLink] = Field(default_factory=list)
    difficulty: str = Field(default="Medium", description="'Easy', 'Medium', or 'Hard'")


class FlashCardCreate(FlashCardBase):
    pass


class FlashCardUpdate(BaseModel):
    front: str | None = None
    back: str | None = None
    application_id: str | None = None
    company: str | None = None
    tags: list[str] | None = None
    links: list[ResourceLink] | None = None
    difficulty: str | None = None


class FlashCardResponse(FlashCardBase):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
