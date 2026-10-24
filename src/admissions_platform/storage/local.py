"""Local-disk document storage.

Physical read/write only — "soft delete" (never actually removing a file
just because an admin clicked delete) is a database-level concern, handled
in ingestion/documents.py by setting/clearing Document.deleted_at. This
module stays swappable for a real cloud backend (GCS, etc.) later without
any caller needing to change, the same shape as the sibling Student
Retention System project's cloud/storage.py — just not built yet, since
nothing here needs it until a real deployment does.
"""
from __future__ import annotations

from admissions_platform.config import STORAGE_DIR


def save_file(applicant_id: int, filename: str, content: bytes) -> str:
    """Writes content to disk under this applicant's folder and returns a
    storage_path relative to STORAGE_DIR (what gets stored in
    Document.storage_path — never an absolute path, so the storage root
    can move without invalidating every row)."""
    applicant_dir = STORAGE_DIR / str(applicant_id)
    applicant_dir.mkdir(parents=True, exist_ok=True)

    dest = applicant_dir / filename
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while dest.exists():
        dest = applicant_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    dest.write_bytes(content)
    return str(dest.relative_to(STORAGE_DIR))


def read_file(storage_path: str) -> bytes:
    return (STORAGE_DIR / storage_path).read_bytes()


def file_exists(storage_path: str) -> bool:
    return (STORAGE_DIR / storage_path).exists()


def purge_file(storage_path: str) -> None:
    """Hard-deletes from disk. Only for permanently purging a document
    after its soft-delete retention window has passed — never called
    directly from the normal delete/restore flow."""
    path = STORAGE_DIR / storage_path
    if path.exists():
        path.unlink()
