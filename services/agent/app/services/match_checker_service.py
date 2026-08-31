"""Real-time JD vs Resume ATS Scanner & Alignment Analysis Engine using Gemini 3.7 Flash & Multi-Models."""

from io import BytesIO
import json
import os
import re
from typing import Any
from pypdf import PdfReader
import structlog
from app.config import settings
from app.services.llm_factory import LLMFactory
from app.services.tailoring_service import ResumeTailoringService

logger = structlog.get_logger()


class MatchCheckerService:
    """Scans and benchmarks raw Job Descriptions against uploaded Resume files & text."""

    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
        """Extract clean plain text from PDF, TXT, or Markdown resume files."""
        if not file_bytes:
            return ""

        lower_name = filename.lower()
        if lower_name.endswith(".pdf"):
            try:
                reader = PdfReader(BytesIO(file_bytes))
                text_parts = []
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_parts.append(extracted)
                return "\n".join(text_parts).strip()
            except Exception as e:
                logger.warning("pdf_extraction_error", filename=filename, error=str(e))
                return file_bytes.decode("utf-8", errors="ignore")

        # TXT or MD files
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore").strip()

    @staticmethod
    async def analyze_match(
        jd_text: str,
        skills_text: str,
        company: str | None = None,
        role: str | None = None,
        model_id: str | None = None,
    ) -> dict[str, Any]:
        """Perform comprehensive JD vs Resume ATS scoring, role alignment, and necessary changes analysis."""
        target_company = company or "Target Company"
        target_role = role or "Software Engineer"

        gemini_key = settings.gemini_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        prompt = f"""
You are a Principal Technical Recruiter and ATS (Applicant Tracking System) Evaluation Expert.
Perform an in-depth audit comparing the candidate's Resume against the target Job Description.

Target Company: {target_company}
Target Role: {target_role}

Candidate Resume:
{skills_text[:5000]}

Target Job Description:
{jd_text[:5000]}

Evaluate real ATS parsing compatibility, keyword density match, and skill gaps.
Return ONLY valid, parseable JSON with this exact schema:
{{
  "ats_score": <calculated ATS score number between 0 and 100>,
  "ats_rating": "<'High Pass (Top 5%)' | 'Competitive Pass' | 'Borderline / Needs Optimization' | 'High Risk / Low Match'>",
  "match_percentage": <number 0 to 100>,
  "verdict": "<'Strong Match' | 'Competitive Match' | 'Stretch Role'>",
  "role_alignment_summary": "<3-sentence executive overview of candidate alignment with {target_company} and {target_role}>",
  "matched_skills": [<string list of matched technical tools, languages, and architectures>],
  "missing_critical_keywords": [<string list of high-priority JD keywords/skills missing from resume that will trigger ATS rejection>],
  "missing_skills": [<string list of secondary preferred skills candidate lacks>],
  "necessary_changes": [
    "<High-priority change 1: Exact section or bullet to rewrite with specific keywords>",
    "<High-priority change 2: Metric/quantification adjustment needed>",
    "<Change 3: Architecture or tool terminology correction to match JD>"
  ],
  "talking_points": [
    "<Talking point 1 highlighting relevant candidate project experience>",
    "<Talking point 2 addressing a core system requirement>",
    "<Talking point 3 bridging an experience gap>"
  ],
  "tailored_bullets": [
    "<Rewritten resume bullet 1 with strong action verb and quantified outcome aligned to this JD>",
    "<Rewritten resume bullet 2 emphasizing scalability and clean architecture>",
    "<Rewritten resume bullet 3 showcasing framework proficiency>"
  ],
  "preparation_roadmap": [
    "<Specific topic or architectural pattern to study before interview 1>",
    "<Specific coding or framework topic to review before interview 2>"
  ]
}}
"""

        # 1. Try Google Gemini directly via google-genai
        if gemini_key and (not model_id or "gemini" in model_id or model_id == "auto"):
            from google import genai

            client = genai.Client(api_key=gemini_key)
            for target_model in ("gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite"):
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
                    logger.info("gemini_ats_check_failed_retrying", model=target_model, error=str(e))

        # 2. Try LangChain LLM (OpenAI / Anthropic)
        llm = LLMFactory.get_llm(model_id)
        if llm:
            try:
                from langchain_core.messages import HumanMessage, SystemMessage

                response = await llm.ainvoke([
                    SystemMessage(content="You are an expert ATS algorithm auditor. Output valid JSON only."),
                    HumanMessage(content=prompt),
                ])
                cleaned = response.content.replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)
                data["model_used"] = model_id or "AI Model"
                return data
            except Exception as e:
                logger.warning("llm_match_check_failed_falling_back", error=str(e))

        # Built-in strict NLP keyword density & ATS parsing engine
        return MatchCheckerService._analyze_with_nlp(
            jd_text=jd_text,
            resume_text=skills_text,
            company=target_company,
            role=target_role,
        )

    @staticmethod
    def _analyze_with_nlp(
        jd_text: str,
        resume_text: str,
        company: str,
        role: str,
    ) -> dict[str, Any]:
        """Real deterministic NLP keyword matching and ATS scoring engine."""
        jd_skills = ResumeTailoringService._extract_skills(jd_text)
        cand_skills = ResumeTailoringService._extract_skills(resume_text)

        for item in re.split(r"[,;\n]+", resume_text):
            cleaned = item.strip().title()
            if cleaned and len(cleaned) > 1 and cleaned not in cand_skills:
                cand_skills.append(cleaned)

        if not jd_skills:
            jd_skills = ["Python", "FastAPI", "Docker", "REST APIs", "SQL", "Git"]

        matched = [s for s in jd_skills if any(s.lower() == c.lower() or c.lower() in s.lower() for c in cand_skills)]
        missing = [s for s in jd_skills if not any(s.lower() == c.lower() or c.lower() in s.lower() for c in cand_skills)]

        total_reqs = max(len(jd_skills), 1)
        score = min(max(float(len(matched) / total_reqs) * 100.0, 40.0), 96.0)

        ats_rating = (
            "High Pass (Top 5%)"
            if score >= 85
            else ("Competitive Pass" if score >= 70 else ("Borderline / Needs Optimization" if score >= 55 else "High Risk / Low Match"))
        )

        verdict = "Strong Match" if score >= 80 else ("Competitive Match" if score >= 65 else "Stretch Role")

        top_matched_str = ", ".join(matched[:3]) or "core software engineering"
        top_missing_str = ", ".join(missing[:2]) if missing else "emerging cloud tools"

        necessary_changes = [
            f"Embed missing core keywords directly in your Work Experience bullets: {', '.join(missing[:3]) if missing else 'Container orchestration & CI/CD pipeline metrics'}.",
            f"Quantify outcomes in your recent projects (e.g. '% reduction in query latency', 'requests/sec throughput handled').",
            f"Align summary title to explicitly reflect '{role}' and emphasize hands-on proficiency in {top_matched_str}.",
        ]

        tailored_bullets = [
            f"Architected scalable backend microservices leveraging {top_matched_str}, optimizing API response times and ensuring reliable data persistence.",
            f"Designed and deployed containerized workloads using Docker, implementing automated testing workflows for high-throughput {role} deliverables.",
            f"Collaborated on full-lifecycle software design, integrating clean architectural patterns and addressing requirements for {company}.",
        ]

        return {
            "ats_score": round(score, 1),
            "ats_rating": ats_rating,
            "match_percentage": round(score, 1),
            "verdict": verdict,
            "role_alignment_summary": (
                f"Candidate resume matches {len(matched)} of {total_reqs} primary technical requirements for {company}'s {role} opening. "
                f"Core strengths include {top_matched_str}. Incorporating missing keywords ({top_missing_str}) will optimize ATS pass rates."
            ),
            "matched_skills": matched,
            "missing_critical_keywords": missing[:4],
            "missing_skills": missing[4:8],
            "necessary_changes": necessary_changes,
            "talking_points": [
                f"Demonstrated track record building production systems with {top_matched_str}.",
                f"Extensive background in asynchronous microservice development and reliable database design.",
                f"Fast learner capable of immediately bridging experience in {missing[0] if missing else 'distributed telemetry'}.",
            ],
            "tailored_bullets": tailored_bullets,
            "preparation_roadmap": [
                f"Review system design tradeoffs and scaling practices applicable to {company}.",
                f"Practice practical coding scenarios emphasizing {matched[0] if matched else 'data structures'}.",
            ],
            "model_used": "Deterministic ATS Matcher",
        }
