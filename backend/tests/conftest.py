import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture(autouse=True)
def _tmp_upload_dir(tmp_path):
    """Redirect uploads to a temp directory for every test."""
    original = settings.upload_dir
    settings.upload_dir = str(tmp_path)
    # Clear the cached property so upload_path re-resolves
    yield
    settings.upload_dir = original


@pytest.fixture
def client():
    """Yield a TestClient instance for the FastAPI app."""
    with TestClient(app) as c:
        yield c
