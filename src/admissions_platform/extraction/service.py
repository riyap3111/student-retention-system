"""Transcript extraction: sends an uploaded transcript PDF to the LLM
client (Gemini's native multimodal PDF understanding, no separate OCR
step) and persists a structured ExtractedTranscript row.

Kept separate from ingestion/documents.py because uploading a file and
extracting its contents are different concerns with different failure
modes - extraction can be retried or re-run with a newer model version
without ever touching the stored document or file.

Uses typing.Optional/List, not `X | None`/`list[X]`: these Pydantic
models are also what Gemini's response_schema is built from, and the
same Python-3.9 annotation-evaluation constraint documented in
models.py applies here too.
"""
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from admissions_platform.llm.client import LLMClient
from admissions_platform.models import Document, ExtractedTranscript
from admissions_platform.storage import local as storage

EXTRACTION_PROMPT = (
    "You are reading a college transcript PDF. Extract the institution "
    "name, the student's cumulative GPA exactly as printed on the "
    "transcript, and every course listed with its course code, title, "
    "credits, grade, and term. If a field is not present on the "
    "transcript, leave it null rather than guessing."
)


class ExtractedCourse(BaseModel):
    code: str
    name: str
    credits: Optional[float] = None
    grade: Optional[str] = None
    term: Optional[str] = None


class TranscriptExtraction(BaseModel):
    institution_name: Optional[str] = None
    cumulative_gpa: Optional[float] = None
    courses: List[ExtractedCourse] = []


def extract_transcript(
    session: Session,
    llm_client: LLMClient,
    document: Document,
    model_version: str = "gemini-2.5-flash",
) -> ExtractedTranscript:
    """Runs extraction for `document` and persists the result. Idempotent
    at the API layer (see api/router.py), not here - this always calls the
    LLM and writes a fresh row, since re-extracting with a specific model
    version on purpose is a legitimate later-phase use case."""
    pdf_bytes = storage.read_file(document.storage_path)
    result = llm_client.extract_structured(EXTRACTION_PROMPT, TranscriptExtraction, pdf_bytes=pdf_bytes)

    extracted = ExtractedTranscript(
        document_id=document.id,
        raw_extraction_json=result.model_dump(),
        institution_name=result.institution_name,
        cumulative_gpa=result.cumulative_gpa,
        courses_json=[course.model_dump() for course in result.courses],
        model_version=model_version,
    )
    session.add(extracted)
    session.commit()
    session.refresh(extracted)
    return extracted
