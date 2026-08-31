import sys
from pathlib import Path

# Ensure services/application and shared are on sys.path
_app_dir = str(Path(__file__).resolve().parent.parent)
_shared_dir = str(Path(__file__).resolve().parent.parent.parent.parent / "shared")
for _p in (_app_dir, _shared_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mongomock.database
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from beanie import init_beanie
from mongomock_motor import AsyncMongoMockClient
from app.main import app
from app.models.application import ApplicationDocument
from app.models.interview_lab import (
    ExperienceDocument,
    FlashCardDocument,
    QuestionDocument,
    TagDocument,
)

# Patch mongomock Database.list_collection_names for PyMongo 4.9+ / Beanie 2.2 compatibility
_orig_list_collections = mongomock.database.Database.list_collection_names


def _patched_list_collection_names(self, *args, **kwargs):
    filter_arg = kwargs.get("filter", None)
    if args:
        filter_arg = args[0]
    return _orig_list_collections(self, filter=filter_arg)


mongomock.database.Database.list_collection_names = _patched_list_collection_names


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    """Initialize an in-memory MongoMock database with Beanie before tests."""
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["test_job_search"]
    await init_beanie(
        database=mock_db,
        document_models=[
            ApplicationDocument,
            TagDocument,
            QuestionDocument,
            ExperienceDocument,
            FlashCardDocument,
        ],
    )
    yield
    await ApplicationDocument.delete_all()
    await TagDocument.delete_all()
    await QuestionDocument.delete_all()
    await ExperienceDocument.delete_all()
    await FlashCardDocument.delete_all()


@pytest_asyncio.fixture
async def app_client():
    """Create an asynchronous HTTP test client against the FastAPI Application Service."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
