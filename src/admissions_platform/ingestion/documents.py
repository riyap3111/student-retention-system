"""Applicant and document CRUD, including soft-delete/restore.

A deleted document is never actually removed from disk or the database —
`Document.deleted_at` is set, and the admin "Trash" view (a later phase's
API/frontend work) can restore it by clearing that column again. Permanent
purging (storage.local.purge_file) is a separate, explicit action never
triggered by this module.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from admissions_platform.models import Applicant, Document
from admissions_platform.storage import local as storage


def create_applicant(session: Session, name: str, email: str, external_ref: str | None = None) -> Applicant:
    applicant = Applicant(name=name, email=email, external_ref=external_ref)
    session.add(applicant)
    session.commit()
    session.refresh(applicant)
    return applicant


def upload_document(
    session: Session, applicant_id: int, filename: str, content: bytes, document_type: str = "transcript"
) -> Document:
    storage_path = storage.save_file(applicant_id, filename, content)
    document = Document(
        applicant_id=applicant_id,
        document_type=document_type,
        original_filename=filename,
        storage_path=storage_path,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


def soft_delete_document(session: Session, document: Document) -> Document:
    document.deleted_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(document)
    return document


def restore_document(session: Session, document: Document) -> Document:
    document.deleted_at = None
    session.commit()
    session.refresh(document)
    return document


def list_active_documents(session: Session, applicant_id: int) -> list[Document]:
    stmt = select(Document).where(Document.applicant_id == applicant_id, Document.deleted_at.is_(None))
    return list(session.scalars(stmt))


def list_trash(session: Session, applicant_id: int | None = None) -> list[Document]:
    stmt = select(Document).where(Document.deleted_at.is_not(None))
    if applicant_id is not None:
        stmt = stmt.where(Document.applicant_id == applicant_id)
    return list(session.scalars(stmt))
