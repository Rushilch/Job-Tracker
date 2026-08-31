"""Business logic service for Job Applications."""

from datetime import datetime
from typing import Any
from beanie import PydanticObjectId
from beanie.operators import RegEx
from shared.schemas.application import (
    ApplicationCreate,
    ApplicationFilter,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationStatusUpdate,
    ApplicationUpdate,
    TimelineEntry,
)
from app.models.application import ApplicationDocument
import structlog

logger = structlog.get_logger()


class ApplicationService:
    """Service handling CRUD and business workflows for job applications."""

    @staticmethod
    async def create_application(payload: ApplicationCreate) -> ApplicationResponse:
        """Create a new application and initialize its timeline."""
        now = datetime.utcnow()
        doc = ApplicationDocument(
            company=payload.company.strip(),
            role=payload.role.strip(),
            job_url=payload.job_url,
            location=payload.location,
            salary_range=payload.salary_range,
            jd_snapshot=payload.jd_snapshot,
            status=payload.status,
            relevance_score=payload.relevance_score,
            notes=payload.notes,
            tags=payload.tags,
            resume_version_id=payload.resume_version_id,
            prep_doc_id=payload.prep_doc_id,
            date_discovered=now,
            date_applied=now if payload.status == ApplicationStatus.APPLIED else None,
            timeline=[
                TimelineEntry(
                    date=now,
                    event=f"Application created in '{payload.status.value}' stage",
                    notes=payload.notes,
                )
            ],
            created_at=now,
            updated_at=now,
        )
        await doc.insert()
        logger.info("application_created", id=str(doc.id), company=doc.company, role=doc.role)
        return doc.to_response_dto()

    @staticmethod
    async def list_applications(filter_params: ApplicationFilter) -> list[ApplicationResponse]:
        """List applications with flexible filtering and pagination."""
        query = ApplicationDocument.find()

        if filter_params.status:
            query = query.find(ApplicationDocument.status == filter_params.status)

        if filter_params.company:
            query = query.find(RegEx(ApplicationDocument.company, filter_params.company, "i"))

        if filter_params.tag:
            query = query.find({"tags": filter_params.tag})

        if filter_params.search:
            # Case-insensitive search on company or role
            regex = filter_params.search
            query = query.find(
                {
                    "$or": [
                        {"company": {"$regex": regex, "$options": "i"}},
                        {"role": {"$regex": regex, "$options": "i"}},
                        {"location": {"$regex": regex, "$options": "i"}},
                    ]
                }
            )

        docs = await query.sort(-ApplicationDocument.created_at).skip(filter_params.offset).limit(filter_params.limit).to_list()
        return [doc.to_response_dto() for doc in docs]

    @staticmethod
    async def get_by_id(app_id: str) -> ApplicationResponse | None:
        """Find an application by ObjectId."""
        if not PydanticObjectId.is_valid(app_id):
            return None
        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        return doc.to_response_dto() if doc else None

    @staticmethod
    async def update_application(app_id: str, payload: ApplicationUpdate) -> ApplicationResponse | None:
        """Update fields of an application."""
        if not PydanticObjectId.is_valid(app_id):
            return None

        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        if not doc:
            return None

        now = datetime.utcnow()
        update_data = payload.model_dump(exclude_unset=True)

        # Check if status changed
        if payload.status is not None and payload.status != doc.status:
            doc.timeline.append(
                TimelineEntry(
                    date=now,
                    event=f"Status changed: {doc.status.value} -> {payload.status.value}",
                    notes=payload.notes,
                )
            )
            if payload.status == ApplicationStatus.APPLIED and not doc.date_applied:
                doc.date_applied = now

        for key, value in update_data.items():
            setattr(doc, key, value)

        doc.updated_at = now
        await doc.save()
        logger.info("application_updated", id=app_id)
        return doc.to_response_dto()

    @staticmethod
    async def update_status(app_id: str, payload: ApplicationStatusUpdate) -> ApplicationResponse | None:
        """Dedicated endpoint to update only the status and record timeline."""
        if not PydanticObjectId.is_valid(app_id):
            return None

        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        if not doc:
            return None

        now = datetime.utcnow()
        old_status = doc.status
        doc.status = payload.status
        doc.updated_at = now

        if payload.status == ApplicationStatus.APPLIED and not doc.date_applied:
            doc.date_applied = now

        doc.timeline.append(
            TimelineEntry(
                date=now,
                event=f"Status changed from {old_status.value} to {payload.status.value}",
                notes=payload.note,
            )
        )

        await doc.save()
        logger.info("application_status_updated", id=app_id, from_status=old_status, to_status=payload.status)
        return doc.to_response_dto()

    @staticmethod
    async def add_timeline_event(app_id: str, entry: TimelineEntry) -> ApplicationResponse | None:
        """Append an event to the timeline of an application."""
        if not PydanticObjectId.is_valid(app_id):
            return None

        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        if not doc:
            return None

        doc.timeline.append(entry)
        doc.updated_at = datetime.utcnow()
        await doc.save()
        return doc.to_response_dto()

    @staticmethod
    async def delete_application(app_id: str) -> bool:
        """Delete an application by ID."""
        if not PydanticObjectId.is_valid(app_id):
            return False

        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        if not doc:
            return False

        await doc.delete()
        logger.info("application_deleted", id=app_id)
        return True

    @staticmethod
    async def upload_resume(app_id: str, file_bytes: bytes, filename: str) -> ApplicationResponse | None:
        """Attach an uploaded resume file and extract its text."""
        if not PydanticObjectId.is_valid(app_id):
            return None

        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        if not doc:
            return None

        extracted_text = ""
        # PDF parsing
        if filename.lower().endswith(".pdf"):
            try:
                import io
                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(file_bytes))
                extracted_text = "\n".join([page.extract_text() or "" for page in reader.pages])
            except Exception as e:
                logger.error("pdf_extraction_failed", error=str(e))
                extracted_text = "PDF parsed (text extraction partial)"
        else:
            try:
                extracted_text = file_bytes.decode("utf-8", errors="ignore")
            except Exception as e:
                extracted_text = f"Attached {filename}"

        now = datetime.utcnow()
        doc.resume_filename = filename
        doc.resume_text = extracted_text
        doc.updated_at = now
        doc.timeline.append(
            TimelineEntry(
                date=now,
                event=f"Resume attached: {filename}",
                notes=f"Extracted {len(extracted_text)} characters of text for AI tailoring",
            )
        )
        await doc.save()
        logger.info("resume_uploaded", id=app_id, filename=filename)
        return doc.to_response_dto()

    @staticmethod
    async def attach_tailored_results(
        app_id: str,
        summary: str,
        bullets: list[str],
        matched_skills: list[str],
        missing_skills: list[str],
        relevance_score: float,
    ) -> ApplicationResponse | None:
        """Store AI tailored resume results on the application."""
        if not PydanticObjectId.is_valid(app_id):
            return None

        doc = await ApplicationDocument.get(PydanticObjectId(app_id))
        if not doc:
            return None

        now = datetime.utcnow()
        doc.tailored_resume_summary = summary
        doc.tailored_bullets = bullets
        doc.matched_skills = matched_skills
        doc.missing_skills = missing_skills
        doc.relevance_score = relevance_score
        doc.updated_at = now
        doc.timeline.append(
            TimelineEntry(
                date=now,
                event=f"AI Resume Tailoring Completed ({relevance_score:.0f}% Match)",
                notes=f"Identified {len(matched_skills)} matching skills and generated {len(bullets)} tailored bullets.",
            )
        )
        await doc.save()
        logger.info("tailored_results_attached", id=app_id, score=relevance_score)
        return doc.to_response_dto()

    @staticmethod
    async def get_stats() -> dict[str, Any]:
        """Aggregate stats for dashboard."""
        all_docs = await ApplicationDocument.find_all().to_list()
        counts_by_status = {status.value: 0 for status in ApplicationStatus}
        for doc in all_docs:
            counts_by_status[doc.status.value] += 1

        return {
            "total_applications": len(all_docs),
            "by_status": counts_by_status,
            "active_pipeline": sum(
                counts_by_status[s.value]
                for s in [
                    ApplicationStatus.DISCOVERED,
                    ApplicationStatus.APPLIED,
                    ApplicationStatus.RESPONDED,
                    ApplicationStatus.INTERVIEW_SCHEDULED,
                ]
            ),
        }
