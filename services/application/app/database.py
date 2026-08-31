"""Database initialization and connection management using PyMongo native async & Beanie."""

from beanie import init_beanie
from pymongo import AsyncMongoClient
import structlog

from app.config import settings
from app.models.application import ApplicationDocument

logger = structlog.get_logger(service=settings.service_name)

mongo_client: AsyncMongoClient | None = None


async def init_db() -> None:
    """Initialize MongoDB connection and Beanie ODM."""
    global mongo_client
    logger.info("connecting_to_mongodb", uri=settings.mongodb_uri, db_name=settings.mongodb_db_name)

    mongo_client = AsyncMongoClient(settings.mongodb_uri)
    db = mongo_client[settings.mongodb_db_name]

    await init_beanie(
        database=db,
        document_models=[
            ApplicationDocument,
        ],
    )
    logger.info("mongodb_and_beanie_initialized")


async def close_db() -> None:
    """Close MongoDB connection on app shutdown."""
    global mongo_client
    if mongo_client:
        await mongo_client.close()
        logger.info("mongodb_connection_closed")
