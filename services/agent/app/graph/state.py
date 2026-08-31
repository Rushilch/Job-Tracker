"""LangGraph State definition for Job Search Automation Pipeline."""

from typing import Annotated, Any, TypedDict
import operator


class AgentPipelineStatus(TypedDict):
    """Execution status and logs for each step."""

    step: str
    status: str
    message: str | None


class JobSearchState(TypedDict):
    """The central state dictionary passed across LangGraph nodes."""

    # Input User Profile & Constraints
    eligibility_profile: dict[str, Any]

    # Module 1: Job Discovery
    raw_listings: list[dict[str, Any]]
    filtered_jobs: list[dict[str, Any]]
    selected_job: dict[str, Any] | None

    # Module 2: Resume Personalization
    base_resume: dict[str, Any] | None
    tailored_resume: dict[str, Any] | None

    # Module 3: Interview & DSA Prep
    prep_doc: dict[str, Any] | None

    # Module 4: GitHub Matcher
    matched_projects: list[dict[str, Any]]

    # Pipeline tracking
    errors: Annotated[list[str], operator.add]
    execution_log: Annotated[list[AgentPipelineStatus], operator.add]
