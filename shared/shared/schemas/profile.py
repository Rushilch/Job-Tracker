"""Pydantic schemas for User Eligibility and Search Profiles."""

from enum import Enum
from pydantic import BaseModel, Field


class SeniorityLevel(str, Enum):
    """Target career stage / seniority level."""

    INTERNSHIP = "internship"
    NEW_GRAD = "new_grad"
    ENTRY_LEVEL = "entry_level"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"


class EligibilityProfile(BaseModel):
    """Stored profile used by the Job Discovery Agent to filter and score postings."""

    target_roles: list[str] = Field(
        default_factory=lambda: [
            "Software Engineer",
            "Entry Level Software Engineer",
            "Software Developer",
            "Full Stack Developer",
            "Backend Engineer",
        ],
        description="Target job titles",
    )
    tech_stack: list[str] = Field(
        default_factory=lambda: [
            "Python",
            "FastAPI",
            "C#",
            ".NET",
            "Java",
            "Angular",
            "TypeScript",
            "Docker",
            "MongoDB",
            "PostgreSQL",
        ],
        description="Core languages and frameworks to prioritize",
    )
    locations: list[str] = Field(
        default_factory=lambda: ["Remote", "Hybrid", "United States", "New York, NY", "San Francisco, CA"],
        description="Preferred locations or work types",
    )
    visa_constraints: str = Field(
        default="Requires sponsorship or OPT/STEM OPT",
        description="Visa/work authorization constraints for filtering",
    )
    seniority: list[SeniorityLevel] = Field(
        default_factory=lambda: [SeniorityLevel.NEW_GRAD, SeniorityLevel.ENTRY_LEVEL, SeniorityLevel.INTERNSHIP]
    )
    min_salary: int | None = Field(default=None, description="Minimum base salary expectation")
    excluded_keywords: list[str] = Field(
        default_factory=lambda: ["Staff", "Principal", "Director", "Lead", "10+ years"],
        description="Keywords to automatically reject/penalize",
    )
