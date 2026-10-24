"""Tests for the admissions-review routes, mounted on the shared FastAPI
app under /admissions (see admissions_platform/api/router.py)."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from student_journey.api.main import app

    with TestClient(app) as c:
        yield c


def test_admissions_health_returns_ok(client):
    response = client.get("/admissions/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
