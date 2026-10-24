"""SQLAlchemy ORM models for the admissions review pipeline.

An ORM (not the sibling project's hand-written schema.sql) because this
schema has many related entities (applicants -> documents -> extracted
transcripts -> validation results -> decisions) that will grow across
several build phases — Alembic migrations evolve it incrementally instead
of rewriting one flat SQL file every phase.

Uses typing.Optional / typing.List rather than the `X | None` / `list[X]`
syntax: SQLAlchemy's declarative mapper evaluates annotations at class-
definition time, and `X | None` isn't evaluable at runtime before Python
3.10 — this project runs on 3.9 (see pyproject.toml).
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DecisionStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    OVERRIDDEN = "overridden"
    NEEDS_INFO = "needs_info"


class Applicant(Base):
    __tablename__ = "applicants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    external_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(back_populates="applicant")
    validation_results: Mapped[list["ValidationResult"]] = relationship(back_populates="applicant")
    course_verifications: Mapped[list["CourseVerification"]] = relationship(back_populates="applicant")
    decision: Mapped[Optional["Decision"]] = relationship(back_populates="applicant", uselist=False)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicants.id"))
    document_type: Mapped[str] = mapped_column(String(50), default="transcript")
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    applicant: Mapped["Applicant"] = relationship(back_populates="documents")
    extracted_transcript: Mapped[Optional["ExtractedTranscript"]] = relationship(
        back_populates="document", uselist=False
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class ExtractedTranscript(Base):
    __tablename__ = "extracted_transcripts"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    raw_extraction_json: Mapped[dict] = mapped_column(JSON)
    institution_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cumulative_gpa: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    courses_json: Mapped[list] = mapped_column(JSON, default=list)
    extraction_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="extracted_transcript")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicants.id"))
    agent_name: Mapped[str] = mapped_column(String(100))
    verdict: Mapped[str] = mapped_column(String(50))  # "pass" | "warning" | "fail"
    issues_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applicant: Mapped["Applicant"] = relationship(back_populates="validation_results")


class AdmissionRule(Base):
    __tablename__ = "admission_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_type: Mapped[str] = mapped_column(String(50))  # "min_gpa" | "required_course" | "max_withdrawals" | ...
    description: Mapped[str] = mapped_column(Text)
    params_json: Mapped[dict] = mapped_column(JSON, default=dict)
    source_handbook_version: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CourseCatalogEntry(Base):
    __tablename__ = "course_catalog"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_code: Mapped[str] = mapped_column(String(20))
    course_name: Mapped[str] = mapped_column(String(255))
    credits: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    prerequisites_json: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(100), default="mock_catalog")
    last_scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CourseVerification(Base):
    __tablename__ = "course_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicants.id"))
    transcript_course_code: Mapped[str] = mapped_column(String(50))
    transcript_course_name: Mapped[str] = mapped_column(String(255))
    matched_catalog_id: Mapped[Optional[int]] = mapped_column(ForeignKey("course_catalog.id"), nullable=True)
    match_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # "matched" | "unmatched" | "ambiguous"

    applicant: Mapped["Applicant"] = relationship(back_populates="course_verifications")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_id: Mapped[int] = mapped_column(ForeignKey("applicants.id"), unique=True)
    ai_recommendation: Mapped[str] = mapped_column(String(50))  # "admit" | "deny" | "needs_info"
    ai_rationale_json: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[DecisionStatus] = mapped_column(Enum(DecisionStatus), default=DecisionStatus.PENDING_REVIEW)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    final_decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    applicant: Mapped["Applicant"] = relationship(back_populates="decision")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column()
    action: Mapped[str] = mapped_column(String(100))
    actor: Mapped[str] = mapped_column(String(200), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
