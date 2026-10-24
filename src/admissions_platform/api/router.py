"""Admissions-review API routes, mounted onto the shared FastAPI app
(student_journey/api/main.py) under the /admissions prefix - one running
process, one port, one set of CORS/rate-limit/Prometheus middleware,
rather than a second standalone app.

Phase 1 (foundation): /admissions/health.
Phase 2 (this phase): applicant creation, transcript upload, and
Gemini-based extraction - POST /admissions/applicants,
POST /admissions/applicants/{id}/documents, GET /admissions/applicants/{id},
POST /admissions/documents/{id}/extract.

Multi-agent validation, handbook rules, course-catalog matching, and the
decision engine are added in later phases.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from admissions_platform.api.deps import get_db_session, get_llm_client
from admissions_platform.api.schemas import (
    ApplicantCreateRequest,
    ApplicantDetailResponse,
    ApplicantResponse,
    DocumentResponse,
    ExtractedTranscriptResponse,
)
from admissions_platform.extraction.service import extract_transcript
from admissions_platform.ingestion.documents import create_applicant, upload_document
from admissions_platform.llm.client import LLMClient
from admissions_platform.models import Applicant, Document

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/applicants", response_model=ApplicantResponse, status_code=status.HTTP_201_CREATED)
def create_applicant_route(
    payload: ApplicantCreateRequest, session: Session = Depends(get_db_session)
) -> Applicant:
    return create_applicant(session, name=payload.name, email=payload.email, external_ref=payload.external_ref)


@router.get("/applicants/{applicant_id}", response_model=ApplicantDetailResponse)
def get_applicant(applicant_id: int, session: Session = Depends(get_db_session)) -> Applicant:
    applicant = session.get(Applicant, applicant_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail=f"Applicant {applicant_id} not found.")
    return applicant


@router.post(
    "/applicants/{applicant_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_route(
    applicant_id: int, file: UploadFile = File(...), session: Session = Depends(get_db_session)
) -> Document:
    applicant = session.get(Applicant, applicant_id)
    if applicant is None:
        raise HTTPException(status_code=404, detail=f"Applicant {applicant_id} not found.")

    is_pdf = file.content_type == "application/pdf" or (file.filename or "").lower().endswith(".pdf")
    if not is_pdf:
        raise HTTPException(status_code=400, detail="Only PDF transcripts are accepted.")

    content = await file.read()
    return upload_document(session, applicant_id, file.filename or "transcript.pdf", content)


@router.post("/documents/{document_id}/extract", response_model=ExtractedTranscriptResponse)
def extract_document_route(
    document_id: int,
    session: Session = Depends(get_db_session),
    llm_client: LLMClient = Depends(get_llm_client),
):
    stmt = select(Document).where(Document.id == document_id)
    document = session.scalars(stmt).first()
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    # Idempotent at this layer: re-posting to an already-extracted document
    # returns the existing result instead of spending another LLM call.
    if document.extracted_transcript is not None:
        return document.extracted_transcript

    return extract_transcript(session, llm_client, document)
