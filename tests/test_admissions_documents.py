"""Tests for the applicant/document service layer, including soft-delete
and restore — a deleted document must disappear from the active list but
remain readable and restorable, never actually gone."""
import admissions_platform.storage.local as storage_local
from admissions_platform.ingestion.documents import (
    create_applicant,
    list_active_documents,
    list_trash,
    restore_document,
    soft_delete_document,
    upload_document,
)


def test_create_applicant_persists_a_row(db_session):
    applicant = create_applicant(db_session, name="Jane Doe", email="jane@example.com")
    assert applicant.id is not None
    assert applicant.name == "Jane Doe"


def test_upload_document_stores_file_and_db_row(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    applicant = create_applicant(db_session, name="Jane Doe", email="jane@example.com")

    document = upload_document(db_session, applicant.id, "transcript.pdf", b"%PDF-content")

    assert document.id is not None
    assert document.applicant_id == applicant.id
    assert storage_local.read_file(document.storage_path) == b"%PDF-content"
    assert document.deleted_at is None


def test_soft_delete_hides_from_active_list_but_keeps_the_file(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    applicant = create_applicant(db_session, name="Jane Doe", email="jane@example.com")
    document = upload_document(db_session, applicant.id, "transcript.pdf", b"content")

    soft_delete_document(db_session, document)

    assert list_active_documents(db_session, applicant.id) == []
    assert [d.id for d in list_trash(db_session, applicant.id)] == [document.id]
    assert storage_local.file_exists(document.storage_path)  # never physically removed by a soft delete


def test_restore_brings_a_deleted_document_back_to_the_active_list(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    applicant = create_applicant(db_session, name="Jane Doe", email="jane@example.com")
    document = upload_document(db_session, applicant.id, "transcript.pdf", b"content")
    soft_delete_document(db_session, document)

    restore_document(db_session, document)

    assert [d.id for d in list_active_documents(db_session, applicant.id)] == [document.id]
    assert list_trash(db_session, applicant.id) == []


def test_list_active_documents_only_returns_this_applicants_documents(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(storage_local, "STORAGE_DIR", tmp_path)
    alice = create_applicant(db_session, name="Alice", email="alice@example.com")
    bob = create_applicant(db_session, name="Bob", email="bob@example.com")
    upload_document(db_session, alice.id, "a.pdf", b"a")
    upload_document(db_session, bob.id, "b.pdf", b"b")

    assert len(list_active_documents(db_session, alice.id)) == 1
    assert len(list_active_documents(db_session, bob.id)) == 1
