import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Yield a TestClient instance for the FastAPI app."""
    with TestClient(app) as c:
        yield c
