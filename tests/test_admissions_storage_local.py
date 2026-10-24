"""Tests for local-disk document storage. STORAGE_DIR is monkeypatched to a
tmp_path so these never touch the real project's storage/ directory."""
import admissions_platform.storage.local as storage


def test_save_and_read_file_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)

    storage_path = storage.save_file(applicant_id=1, filename="transcript.pdf", content=b"%PDF-fake-content")

    assert storage.file_exists(storage_path)
    assert storage.read_file(storage_path) == b"%PDF-fake-content"


def test_save_file_avoids_overwriting_a_same_named_file(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)

    path1 = storage.save_file(applicant_id=1, filename="transcript.pdf", content=b"first")
    path2 = storage.save_file(applicant_id=1, filename="transcript.pdf", content=b"second")

    assert path1 != path2
    assert storage.read_file(path1) == b"first"
    assert storage.read_file(path2) == b"second"


def test_purge_file_removes_it_from_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)

    storage_path = storage.save_file(applicant_id=2, filename="doc.pdf", content=b"data")
    assert storage.file_exists(storage_path)

    storage.purge_file(storage_path)
    assert not storage.file_exists(storage_path)


def test_purge_file_is_a_noop_if_already_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "STORAGE_DIR", tmp_path)
    storage.purge_file("applicant-99/never-existed.pdf")  # should not raise
