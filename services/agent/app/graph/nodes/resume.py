"""Module 2: Real Resume Personalization Agent Node.

Re-ranks and tailors resume bullet points against the specific JD snapshot
using Multi-Model LLM reasoning (Gemini / OpenAI / Claude).
"""

from typing import Any
import structlog
from app.graph.state import JobSearchState
from app.services.tailoring_service import ResumeTailoringService

logger = structlog.get_logger()


async def tailor_resume_node(state: JobSearchState) -> dict[str, Any]:
    """LangGraph node: transforms base resume into tailored version for selected job."""
    selected_job = state.get("selected_job") or {}
    company = selected_job.get("company", "Target Company")
    role = selected_job.get("role", "Software Engineer")
    jd_snapshot = selected_job.get("jd_snapshot", "")

    base_resume = state.get("base_resume")
    resume_text = ""
    if isinstance(base_resume, dict):
        resume_text = base_resume.get("raw_text") or str(base_resume)
    elif isinstance(base_resume, str):
        resume_text = base_resume

    if not resume_text:
        resume_text = "Proficient in Python, FastAPI, Docker, C#, Angular, TypeScript, PostgreSQL, MongoDB, Git, CI/CD, and Microservices architecture."

    logger.info("executing_real_resume_tailoring", company=company, role=role)

    tailored_result = await ResumeTailoringService.tailor_resume(
        company=company,
        role=role,
        jd_text=jd_snapshot,
        resume_text=resume_text,
    )

    tailored_resume_doc = {
        "company": company,
        "role": role,
        "summary": tailored_result.get("tailored_summary"),
        "bullet_points": tailored_result.get("tailored_bullets", []),
        "matched_skills": tailored_result.get("matched_skills", []),
        "missing_skills": tailored_result.get("missing_skills", []),
        "relevance_score": tailored_result.get("relevance_score", 85.0),
        "model_used": tailored_result.get("model_used", "AI Model"),
    }

    return {
        "tailored_resume": tailored_resume_doc,
        "execution_log": state.get("execution_log", []) + [
            {
                "step": "resume_tailoring",
                "status": "completed",
                "message": f"Tailored resume for {role} at {company} (Match Score: {tailored_resume_doc['relevance_score']}%).",
            }
        ],
    }
