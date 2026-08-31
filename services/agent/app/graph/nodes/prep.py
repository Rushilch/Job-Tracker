"""Module 3: Real Interview & DSA Prep Agent Node.

Researches past interview questions (Glassdoor, LeetCode, company interview loops)
and builds a comprehensive structured prep kit for the target company.
"""

from typing import Any
import structlog
from app.graph.state import JobSearchState
from app.services.interview_prep_service import InterviewPrepService

logger = structlog.get_logger()


async def generate_interview_prep_node(state: JobSearchState) -> dict[str, Any]:
    """LangGraph node: researches company & role patterns and synthesizes real prep document."""
    selected_job = state.get("selected_job") or {}
    company = selected_job.get("company", "Target Company")
    role = selected_job.get("role", "Software Engineer")
    jd_snapshot = selected_job.get("jd_snapshot", "")

    logger.info("executing_real_interview_prep_node", company=company, role=role)

    prep_data = await InterviewPrepService.generate_prep_doc(
        company=company,
        role=role,
        jd_text=jd_snapshot,
    )

    dsa_count = len(prep_data.get("dsa_questions", []))
    sys_design_count = len(prep_data.get("system_design_topics", []))

    return {
        "prep_doc": prep_data,
        "execution_log": state.get("execution_log", []) + [
            {
                "step": "interview_prep",
                "status": "completed",
                "message": f"Generated comprehensive interview kit for {company}: {dsa_count} DSA questions, {sys_design_count} System Design topics, and STAR behavioral guides.",
            }
        ],
    }
