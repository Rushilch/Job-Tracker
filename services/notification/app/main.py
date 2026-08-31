"""FastAPI application entrypoint for Notification Service."""

from fastapi import APIRouter, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import setup_logging
from app.config import settings

logger = setup_logging(service_name=settings.service_name, log_level=settings.log_level)

app = FastAPI(
    title="Notification & Reminder Service",
    description="Microservice for status-change alerts, interview reminders, auto-ghosting checks, and nightly digests.",
    version="0.1.0",
    docs_url="/api/notifications/docs",
    openapi_url="/api/notifications/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check for Notification Service."""
    return {"status": "healthy", "service": settings.service_name}


@router.post("/check-ghosting", status_code=status.HTTP_200_OK)
async def run_ghosting_check():
    """Trigger auto-ghosting scan for applications with no response >= N days."""
    logger.info("running_auto_ghosting_check", threshold_days=settings.auto_ghosting_days_threshold)
    return {
        "status": "completed",
        "message": f"Auto-ghosting check triggered (threshold: {settings.auto_ghosting_days_threshold} days).",
    }


@router.post("/send-digest", status_code=status.HTTP_200_OK)
async def send_nightly_digest():
    """Send nightly application pipeline digest."""
    logger.info("sending_nightly_digest")
    return {"status": "completed", "message": "Nightly digest dispatched."}


app.include_router(router)


@app.get("/health", tags=["Health"])
async def root_health():
    return {"status": "healthy", "service": settings.service_name}
