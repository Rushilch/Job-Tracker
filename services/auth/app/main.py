"""Auth Service application entrypoint.

This service manages authentication, OAuth 2.0 flows, and user tokens.
Planned implementation for Step 6:
- FastAPI Security (OAuth2PasswordBearer, HTTPBearer)
- joserfc for JWT/JWS issuance and token verification
- pwdlib[argon2] (Argon2id) for password hashing
"""

from fastapi import APIRouter, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from shared.logging import setup_logging
from app.config import settings

logger = setup_logging(service_name=settings.service_name, log_level=settings.log_level)

app = FastAPI(
    title="Auth Service",
    description="Authentication and Token Management Service",
    version="0.1.0",
    docs_url="/api/auth/docs",
    openapi_url="/api/auth/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check for Auth Service."""
    return {"status": "healthy", "service": settings.service_name}


@router.post("/login", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def login_stub():
    """Login endpoint stub (to be implemented in Step 6 with joserfc & Argon2id)."""
    return {
        "detail": "Auth will be implemented in Step 6. Endpoints are currently open in Step 1."
    }


@router.post("/register", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def register_stub():
    """Register endpoint stub."""
    return {
        "detail": "Auth will be implemented in Step 6. Endpoints are currently open in Step 1."
    }


app.include_router(router)


@app.get("/health", tags=["Health"])
async def root_health():
    return {"status": "healthy", "service": settings.service_name}
