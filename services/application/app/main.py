"""FastAPI application entrypoint for Application Service."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import setup_logging
from app.config import settings
from app.database import close_db, init_db
from app.routes.applications import router as applications_router

logger = setup_logging(service_name=settings.service_name, log_level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan context manager for startup and shutdown."""
    logger.info("starting_application_service", port=settings.service_port)
    await init_db()
    yield
    logger.info("shutting_down_application_service")
    await close_db()


app = FastAPI(
    title="Application Tracker Service",
    description="Microservice for tracking job applications, statuses, interviews, and notes.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/applications/docs",
    openapi_url="/api/applications/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open in development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(applications_router)


@app.get("/health", tags=["Health"])
async def root_health():
    """Root health check for the service."""
    return {"status": "healthy", "service": settings.service_name}
