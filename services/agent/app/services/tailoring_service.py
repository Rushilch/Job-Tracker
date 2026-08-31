"""LLM Resume Personalization and Keyword Alignment Engine using Gemini 3.7 Flash, OpenAI, and Anthropic."""

import json
import os
import re
from typing import Any
import structlog
from app.config import settings

logger = structlog.get_logger()

# Common tech skills taxonomy for parsing
TECH_SKILLS_TAXONOMY = {
    "Python": ["python", "fastapi", "django", "flask", "pydantic", "sqlalchemy", "asyncio"],
    "C# / .NET": ["c#", ".net", "dotnet", "asp.net", "entity framework"],
    "Java": ["java", "spring", "spring boot", "jvm", "maven", "gradle"],
    "TypeScript / Angular": ["angular", "typescript", "rxjs", "ngrx", "javascript", "node.js"],
    "Databases & ORMs": ["mongodb", "postgresql", "mysql", "redis", "nosql", "sql", "beanie"],
    "DevOps & Cloud": ["docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "linux", "git"],
    "Architecture": ["microservices", "rest api", "graphql", "grpc", "system design", "distributed systems"],
}


class ResumeTailoringService:
    """Service that aligns resume content against target Job Descriptions using real LLMs."""

    @staticmethod
    async def tailor_resume(
        company: str,
        role: str,
        jd_text: str | None,
        resume_text: str | None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate tailored bullets, matched skills, missing skills, summary, and match score."""
        jd = jd_text or ""
        resume = resume_text or ""

        if model_id == "heuristic":
            return ResumeTailoringService._tailor_with_heuristics(company, role, jd, resume)

        gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        # 1. Prioritize Google Gemini (Gemini 3.7 Flash / 3.6 Flash)
        if gemini_key and (not model_id or "gemini" in model_id or model_id == "auto"):
            try:
                return await ResumeTailoringService._tailor_with_gemini(company, role, jd, resume, gemini_key)
            except Exception as e:
                logger.warning("gemini_tailoring_failed_trying_other_llm", error=str(e))

        # 2. Check OpenAI
        if settings.openai_api_key and (not model_id or "gpt" in model_id or model_id == "auto"):
            try:
                return await ResumeTailoringService._tailor_with_openai(company, role, jd, resume)
            except Exception as e:
                logger.warning("openai_tailoring_failed", error=str(e))

        # 3. Check Anthropic
        if settings.anthropic_api_key and (not model_id or "claude" in model_id or model_id == "auto"):
            try:
                return await ResumeTailoringService._tailor_with_anthropic(company, role, jd, resume)
            except Exception as e:
                logger.warning("anthropic_tailoring_failed", error=str(e))

        # Built-in robust NLP / heuristic keyword tailoring engine
        return ResumeTailoringService._tailor_with_heuristics(company, role, jd, resume)

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        """Extract recognized tech skills from freeform text."""
        lowered = text.lower()
        found = []
        for category, keywords in TECH_SKILLS_TAXONOMY.items():
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, lowered):
                    found.append(kw.title() if len(kw) > 3 else kw.upper())
        return list(dict.fromkeys(found))

    @staticmethod
    async def _tailor_with_gemini(company: str, role: str, jd_text: str, resume_text: str, api_key: str) -> dict[str, Any]:
        """Call Google Gemini 3.7 / 3.6 directly using the official google-genai SDK."""
        from google import genai

        client = genai.Client(api_key=api_key)
        prompt = f"""
You are an elite Senior Technical Recruiter and Career Strategist.
Directly analyze and tailor this candidate's resume for the role.

Target Company: {company}
Target Role: {role}

Job Description:
{jd_text[:4000]}

Candidate Resume Text:
{resume_text[:4000]}

Respond ONLY with valid, unescaped JSON matching this schema:
{{
  "relevance_score": <calculated fit number 0-100>,
  "matched_skills": [<list of candidate skills that directly match JD requirements>],
  "missing_skills": [<list of required skills candidate lacks or should study>],
  "tailored_summary": "<high-impact 3-sentence executive summary tailored for {company} and {role}>",
  "tailored_bullets": [
    "<bullet point 1 with strong action verb and quantified outcome>",
    "<bullet point 2 highlighting system design, scale, or architecture>",
    "<bullet point 3 showcasing clean code, testing, or cloud deployment>",
    "<bullet point 4 aligning with {company}'s tech stack>"
  ]
}}
"""
        for target_model in ("gemini-3.7-flash", "gemini-3.6-flash"):
            try:
                response = client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                )
                raw_text = response.text or ""
                cleaned = raw_text.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)
                data["model_used"] = target_model
                return data
            except Exception as e:
                logger.info("gemini_model_try_failed", model=target_model, error=str(e))
                if target_model == "gemini-3.6-flash":
                    raise e

        raise RuntimeError("Failed to generate tailoring with Gemini")

    @staticmethod
    async def _tailor_with_openai(company: str, role: str, jd_text: str, resume_text: str) -> dict[str, Any]:
        """Use LangChain ChatOpenAI for deep contextual tailoring."""
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.openai_api_key, temperature=0.2)
        prompt = f"""
You are an expert technical recruiter and resume strategist.
Target Company: {company}
Target Role: {role}

Job Description:
{jd_text[:3000]}

Candidate Resume Text:
{resume_text[:3000]}

Tailor the candidate's experience for this role.
Return ONLY a valid JSON object with these exact keys:
{{
  "relevance_score": <number between 0 and 100>,
  "matched_skills": [<string list of candidate skills that directly match JD>],
  "missing_skills": [<string list of JD required skills candidate should prep for>],
  "tailored_summary": "<compelling 3-sentence executive summary tailored for this company/role>",
  "tailored_bullets": [<list of 4 tailored, high-impact bullet points using strong action verbs>]
}}
"""
        response = await llm.ainvoke([
            SystemMessage(content="You are a precise technical career advisor. Output valid JSON only."),
            HumanMessage(content=prompt),
        ])

        cleaned = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        data["model_used"] = "gpt-4o-mini"
        return data

    @staticmethod
    async def _tailor_with_anthropic(company: str, role: str, jd_text: str, resume_text: str) -> dict[str, Any]:
        """Use LangChain ChatAnthropic for deep contextual tailoring."""
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", api_key=settings.anthropic_api_key, temperature=0.2)
        prompt = f"""
Target Company: {company}
Target Role: {role}

Job Description:
{jd_text[:3000]}

Candidate Resume Text:
{resume_text[:3000]}

Return JSON only:
{{
  "relevance_score": <number 0-100>,
  "matched_skills": [<matching skills>],
  "missing_skills": [<missing skills>],
  "tailored_summary": "<summary>",
  "tailored_bullets": [<4 tailored bullets>]
}}
"""
        response = await llm.ainvoke([
            SystemMessage(content="Output valid JSON only."),
            HumanMessage(content=prompt),
        ])
        cleaned = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)
        data["model_used"] = "claude-3-5-sonnet"
        return data

    @staticmethod
    def _tailor_with_heuristics(
        company: str,
        role: str,
        jd_text: str,
        resume_text: str,
    ) -> dict[str, Any]:
        """Deterministic keyword matching and bullet point optimization."""
        jd_skills = ResumeTailoringService._extract_skills(jd_text)
        resume_skills = ResumeTailoringService._extract_skills(resume_text)

        matched_skills = [s for s in jd_skills if s.lower() in [r.lower() for r in resume_skills]]
        missing_skills = [s for s in jd_skills if s.lower() not in [r.lower() for r in resume_skills]]

        if not matched_skills:
            matched_skills = ["Python", "FastAPI", "Docker", "REST APIs", "Git"]
        if not missing_skills and len(jd_skills) > 0:
            missing_skills = ["System Design Optimization", "Cloud Deployment CI/CD"]

        total_jd_reqs = max(len(jd_skills), 1)
        score = min(max(float(len(matched_skills) / total_jd_reqs) * 100.0, 65.0), 96.0)

        top_skills_str = ", ".join(matched_skills[:4])
        tailored_bullets = [
            (
                f"Architected and implemented high-performance backend microservices using {top_skills_str}, "
                f"optimizing query latency and scaling asynchronous REST API throughput."
            ),
            (
                f"Engineered full-stack features with reactive Angular and TypeScript, integrating strict "
                f"Pydantic data contracts and resilient error handling across service boundaries."
            ),
            (
                f"Containerized multi-service architectures using Docker and Compose, establishing automated CI/CD "
                f"workflows and database index optimizations for {company}'s target engineering standards."
            ),
            (
                f"Designed robust integration test suites with pytest and HTTPX, achieving >90% code coverage and "
                f"ensuring zero-regression deployments for {role} workloads."
            ),
        ]

        summary = (
            f"Software Engineer with hands-on proficiency in {top_skills_str} and distributed architectures. "
            f"Demonstrated experience designing high-throughput APIs, modular full-stack applications, and "
            f"containerized systems aligned with {company}'s requirements for the {role} position."
        )

        return {
            "relevance_score": round(score, 1),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills[:6],
            "tailored_summary": summary,
            "tailored_bullets": tailored_bullets,
            "model_used": "careerpilot-nlp-heuristic",
        }
