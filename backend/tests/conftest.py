import asyncio

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import init_db
from app.main import app


@pytest.fixture(autouse=True)
def _tmp_dirs(tmp_path):
    """Redirect uploads and DB to a temp directory for every test."""
    original_upload = settings.upload_dir
    original_db = settings.db_path
    settings.upload_dir = str(tmp_path / "uploads")
    settings.db_path = str(tmp_path / "test.db")
    (tmp_path / "uploads").mkdir()
    asyncio.run(init_db())
    yield
    settings.upload_dir = original_upload
    settings.db_path = original_db


@pytest.fixture
def client():
    """Yield a TestClient instance for the FastAPI app."""
    with TestClient(app) as c:
        yield c
