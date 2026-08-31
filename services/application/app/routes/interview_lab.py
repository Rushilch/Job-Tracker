"""FastAPI route endpoints for Interview Lab: Tags, Questions, Experiences, Flash Cards, and Excel Export."""

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.services.interview_lab_service import InterviewLabService
from shared.schemas.interview_lab import (
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    FlashCardCreate,
    FlashCardResponse,
    FlashCardUpdate,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    TagCreate,
    TagResponse,
    TagUpdate,
)

router = APIRouter(prefix="/api/interview-lab", tags=["Interview Lab"])


# -------------------------------------------------------------------------
# Tags Endpoints
# -------------------------------------------------------------------------
@router.get("/tags", response_model=list[TagResponse])
async def list_tags():
    """Retrieve all user-created taxonomy tags."""
    return await InterviewLabService.list_tags()


@router.post("/tags", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate):
    """Create a new taxonomy tag or return existing."""
    return await InterviewLabService.create_tag(payload)


@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: str, payload: TagUpdate):
    """Update a taxonomy tag's name or color."""
    tag = await InterviewLabService.update_tag(tag_id, payload)
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag {tag_id} not found")
    return tag


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: str):
    """Delete a taxonomy tag."""
    success = await InterviewLabService.delete_tag(tag_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tag {tag_id} not found")


# -------------------------------------------------------------------------
# Questions Endpoints
# -------------------------------------------------------------------------
@router.get("/questions", response_model=list[QuestionResponse])
async def list_questions(
    application_id: str | None = Query(default=None, description="Filter by linked job application ID"),
    company: str | None = Query(default=None, description="Filter by company name"),
    difficulty: str | None = Query(default=None, description="'Easy', 'Medium', 'Hard', or 'All'"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    search: str | None = Query(default=None, description="Search term across title, topic, notes"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List DSA/LeetCode questions with optional filters."""
    return await InterviewLabService.list_questions(
        application_id=application_id,
        company=company,
        difficulty=difficulty,
        tag=tag,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.post("/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(payload: QuestionCreate):
    """Create a new DSA question with multiple solutions and complexity notes."""
    return await InterviewLabService.create_question(payload)


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str):
    """Get single DSA question by ID."""
    q = await InterviewLabService.get_question(question_id)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")
    return q


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(question_id: str, payload: QuestionUpdate):
    """Update a question, its solutions, or complexity analysis."""
    q = await InterviewLabService.update_question(question_id, payload)
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")
    return q


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: str):
    """Delete a question."""
    success = await InterviewLabService.delete_question(question_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Question {question_id} not found")


# -------------------------------------------------------------------------
# Experiences Endpoints
# -------------------------------------------------------------------------
@router.get("/experiences", response_model=list[ExperienceResponse])
async def list_experiences(
    application_id: str | None = Query(default=None, description="Filter by linked job application ID"),
    company: str | None = Query(default=None, description="Search by company name"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    min_rating: int | None = Query(default=None, ge=1, le=10, description="Minimum self-rating"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List interview experience logs."""
    return await InterviewLabService.list_experiences(
        application_id=application_id,
        company=company,
        tag=tag,
        min_rating=min_rating,
        limit=limit,
        offset=offset,
    )


@router.post("/experiences", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(payload: ExperienceCreate):
    """Log a new interview experience with pipeline rounds, Q&As, and self-rating."""
    return await InterviewLabService.create_experience(payload)


@router.get("/experiences/{exp_id}", response_model=ExperienceResponse)
async def get_experience(exp_id: str):
    """Get single interview experience by ID."""
    exp = await InterviewLabService.get_experience(exp_id)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experience {exp_id} not found")
    return exp


@router.put("/experiences/{exp_id}", response_model=ExperienceResponse)
async def update_experience(exp_id: str, payload: ExperienceUpdate):
    """Update an interview experience."""
    exp = await InterviewLabService.update_experience(exp_id, payload)
    if not exp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experience {exp_id} not found")
    return exp


@router.delete("/experiences/{exp_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(exp_id: str):
    """Delete an interview experience."""
    success = await InterviewLabService.delete_experience(exp_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Experience {exp_id} not found")


# -------------------------------------------------------------------------
# Flash Cards Endpoints
# -------------------------------------------------------------------------
@router.get("/flashcards", response_model=list[FlashCardResponse])
async def list_flashcards(
    application_id: str | None = Query(default=None, description="Filter by linked job application ID"),
    company: str | None = Query(default=None, description="Filter by company name"),
    tag: str | None = Query(default=None, description="Filter by tag"),
    difficulty: str | None = Query(default=None, description="'Easy', 'Medium', 'Hard', or 'All'"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List manual flashcards."""
    return await InterviewLabService.list_flashcards(
        application_id=application_id,
        company=company,
        tag=tag,
        difficulty=difficulty,
        limit=limit,
        offset=offset,
    )


@router.get("/flashcards/study", response_model=list[FlashCardResponse])
async def get_study_deck(
    application_id: str | None = Query(default=None),
    count: int = Query(default=20, ge=1, le=200),
    tag: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    shuffle: bool = Query(default=True),
):
    """Get a prepared deck of flashcards for active study."""
    return await InterviewLabService.get_study_deck(
        application_id=application_id, count=count, tag=tag, difficulty=difficulty, shuffle=shuffle
    )


@router.post("/flashcards", response_model=FlashCardResponse, status_code=status.HTTP_201_CREATED)
async def create_flashcard(payload: FlashCardCreate):
    """Create a new manual revision flashcard."""
    return await InterviewLabService.create_flashcard(payload)


@router.get("/flashcards/{card_id}", response_model=FlashCardResponse)
async def get_flashcard(card_id: str):
    """Get single flashcard by ID."""
    fc = await InterviewLabService.get_flashcard(card_id)
    if not fc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flashcard {card_id} not found")
    return fc


@router.put("/flashcards/{card_id}", response_model=FlashCardResponse)
async def update_flashcard(card_id: str, payload: FlashCardUpdate):
    """Update a flashcard."""
    fc = await InterviewLabService.update_flashcard(card_id, payload)
    if not fc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flashcard {card_id} not found")
    return fc


@router.delete("/flashcards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flashcard(card_id: str):
    """Delete a flashcard."""
    success = await InterviewLabService.delete_flashcard(card_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Flashcard {card_id} not found")


# -------------------------------------------------------------------------
# Excel Export Endpoint
# -------------------------------------------------------------------------
@router.get("/export/excel")
async def export_interview_lab_excel(
    application_id: str | None = Query(default=None),
    company: str | None = Query(default=None),
):
    """Export Interview Lab experiences, questions, and flashcards to a styled Excel (.xlsx) file."""
    excel_bytes = await InterviewLabService.export_excel(application_id=application_id, company=company)
    company_slug = f"_{company.lower().replace(' ', '_')}" if company else ""
    filename = f"interview_lab_notes{company_slug}.xlsx"
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
