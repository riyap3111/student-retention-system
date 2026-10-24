"""Tests for the transcript-extraction service layer: given an uploaded
document and a (fake) LLM client, extraction must persist a correctly
shaped ExtractedTranscript row and send the document's actual PDF bytes
to the LLM - never a real network call to Gemini."""
import admissions_platform.storage.local as storage_local
from admissions_platform.extraction.service import (
    EXTRACTION_PROMPT,
    ExtractedCourse,
    TranscriptExtraction,
    extract_transcript,
)
from admissions_platform.ingestion.documents import create_applicant, upload_document
from admissions_platform.llm.client import FakeLLMClient


def _upload_fake_transcript(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    applicant = create_applicant(db_session, name="Jane Doe", email="jane@example.com")
    return upload_document(db_session, applicant.id, "transcript.pdf", b"%PDF-fake-bytes")


def test_extract_transcript_persists_structured_fields(db_session, tmp_path, monkeypatch):
    document = _upload_fake_transcript(db_session, tmp_path, monkeypatch)
    fake_client = FakeLLMClient(
        responses=[
            TranscriptExtraction(
                institution_name="Meridian Community College",
                cumulative_gpa=3.42,
                courses=[ExtractedCourse(code="CS101", name="Introduction to Programming", credits=3.0, grade="A")],
            )
        ]
    )

    extracted = extract_transcript(db_session, fake_client, document)

    assert extracted.document_id == document.id
    assert extracted.institution_name == "Meridian Community College"
    assert extracted.cumulative_gpa == 3.42
    assert extracted.courses_json == [
        {"code": "CS101", "name": "Introduction to Programming", "credits": 3.0, "grade": "A", "term": None}
    ]
    assert extracted.model_version == "gemini-2.5-flash"


def test_extract_transcript_sends_the_actual_pdf_bytes_to_the_llm(db_session, tmp_path, monkeypatch):
    document = _upload_fake_transcript(db_session, tmp_path, monkeypatch)
    fake_client = FakeLLMClient(responses=[TranscriptExtraction()])

    extract_transcript(db_session, fake_client, document)

    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["prompt"] == EXTRACTION_PROMPT
    assert call["response_model"] is TranscriptExtraction
    assert call["had_pdf"] is True
    assert call["had_text"] is False


def test_extract_transcript_with_no_courses_still_persists(db_session, tmp_path, monkeypatch):
    document = _upload_fake_transcript(db_session, tmp_path, monkeypatch)
    fake_client = FakeLLMClient(responses=[TranscriptExtraction(institution_name=None, cumulative_gpa=None)])

    extracted = extract_transcript(db_session, fake_client, document)

    assert extracted.institution_name is None
    assert extracted.cumulative_gpa is None
    assert extracted.courses_json == []
