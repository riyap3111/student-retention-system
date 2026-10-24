"""Tests for the admissions-review routes, mounted on the shared FastAPI
app under /admissions (see admissions_platform/api/router.py).

Phase 2's routes (applicant creation, document upload, extraction) are
exercised end-to-end through the real app, with the DB session and LLM
client swapped out via FastAPI dependency_overrides - a disposable
per-test SQLite database and a FakeLLMClient, never a real network call."""
import pytest
from fastapi.testclient import TestClient

import admissions_platform.storage.local as storage_local
from admissions_platform.api.deps import get_db_session, get_llm_client
from admissions_platform.extraction.service import ExtractedCourse, TranscriptExtraction
from admissions_platform.llm.client import FakeLLMClient


@pytest.fixture
def fake_llm_client():
    return FakeLLMClient()


@pytest.fixture
def client(db_session, fake_llm_client, tmp_path, monkeypatch):
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    from student_journey.api.main import app

    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    app.dependency_overrides[get_llm_client] = lambda: fake_llm_client
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def test_admissions_health_returns_ok(client):
    response = client.get("/admissions/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_applicant_returns_201_with_id(client):
    response = client.post("/admissions/applicants", json={"name": "Jane Doe", "email": "jane@example.com"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Jane Doe"
    assert body["id"] is not None


def test_get_applicant_404_when_missing(client):
    response = client.get("/admissions/applicants/999")
    assert response.status_code == 404


def test_upload_document_rejects_non_pdf(client):
    applicant_id = client.post(
        "/admissions/applicants", json={"name": "Jane Doe", "email": "jane@example.com"}
    ).json()["id"]

    response = client.post(
        f"/admissions/applicants/{applicant_id}/documents",
        files={"file": ("transcript.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_document_404_when_applicant_missing(client):
    response = client.post(
        "/admissions/applicants/999/documents",
        files={"file": ("transcript.pdf", b"%PDF-content", "application/pdf")},
    )
    assert response.status_code == 404


def test_full_upload_and_extract_flow(client, fake_llm_client):
    fake_llm_client.queue(
        TranscriptExtraction(
            institution_name="Meridian Community College",
            cumulative_gpa=3.5,
            courses=[ExtractedCourse(code="CS101", name="Introduction to Programming", credits=3.0, grade="A")],
        )
    )

    applicant_id = client.post(
        "/admissions/applicants", json={"name": "Jane Doe", "email": "jane@example.com"}
    ).json()["id"]

    document = client.post(
        f"/admissions/applicants/{applicant_id}/documents",
        files={"file": ("transcript.pdf", b"%PDF-content", "application/pdf")},
    ).json()
    assert document["original_filename"] == "transcript.pdf"

    extracted = client.post(f"/admissions/documents/{document['id']}/extract").json()
    assert extracted["institution_name"] == "Meridian Community College"
    assert extracted["cumulative_gpa"] == 3.5
    assert extracted["courses_json"][0]["code"] == "CS101"

    detail = client.get(f"/admissions/applicants/{applicant_id}").json()
    assert detail["documents"][0]["extracted_transcript"]["institution_name"] == "Meridian Community College"


def test_extract_is_idempotent_and_does_not_call_the_llm_twice(client, fake_llm_client):
    fake_llm_client.queue(TranscriptExtraction(institution_name="First Call"))

    applicant_id = client.post(
        "/admissions/applicants", json={"name": "Jane Doe", "email": "jane@example.com"}
    ).json()["id"]
    document_id = client.post(
        f"/admissions/applicants/{applicant_id}/documents",
        files={"file": ("transcript.pdf", b"%PDF-content", "application/pdf")},
    ).json()["id"]

    first = client.post(f"/admissions/documents/{document_id}/extract").json()
    second = client.post(f"/admissions/documents/{document_id}/extract").json()

    assert first == second
    assert len(fake_llm_client.calls) == 1


def test_extract_404_when_document_missing(client):
    response = client.post("/admissions/documents/999/extract")
    assert response.status_code == 404


def test_extract_returns_503_when_no_llm_client_is_configured(db_session, tmp_path, monkeypatch):
    """With get_llm_client NOT overridden, a missing GEMINI_API_KEY must
    surface as a clean 503 (expected unconfigured state), not a raw 500."""
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from student_journey.api.main import app

    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session
    try:
        with TestClient(app) as c:
            applicant_id = c.post(
                "/admissions/applicants", json={"name": "Jane Doe", "email": "jane@example.com"}
            ).json()["id"]
            document_id = c.post(
                f"/admissions/applicants/{applicant_id}/documents",
                files={"file": ("transcript.pdf", b"%PDF-content", "application/pdf")},
            ).json()["id"]

            response = c.post(f"/admissions/documents/{document_id}/extract")
            assert response.status_code == 503
            assert "GEMINI_API_KEY" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
