"""Pydantic request/response models for the admissions API routes.

Separate from both models.py (the ORM layer) and extraction/service.py's
TranscriptExtraction (the LLM's response shape) - these are what the HTTP
boundary actually speaks, built with `from_attributes=True` so a route can
return a SQLAlchemy row directly.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ApplicantCreateRequest(BaseModel):
    name: str
    email: str
    external_ref: Optional[str] = None


class ApplicantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    external_ref: Optional[str] = None
    created_at: datetime


class ExtractedCourseResponse(BaseModel):
    code: str
    name: str
    credits: Optional[float] = None
    grade: Optional[str] = None
    term: Optional[str] = None


class ExtractedTranscriptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    institution_name: Optional[str] = None
    cumulative_gpa: Optional[float] = None
    courses_json: List[ExtractedCourseResponse] = []
    model_version: str
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    applicant_id: int
    document_type: str
    original_filename: str
    uploaded_at: datetime
    extracted_transcript: Optional[ExtractedTranscriptResponse] = None


class ApplicantDetailResponse(ApplicantResponse):
    documents: List[DocumentResponse] = []
