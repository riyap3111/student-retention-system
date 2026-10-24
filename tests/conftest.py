"""Shared pytest fixtures.

Every test runs against a fresh temp-file SQLite database via the same
SQLAlchemy engine abstraction db.py uses for real Postgres — tables created
directly from the ORM models (Base.metadata.create_all), not through
Alembic, since tests want a fast, disposable schema rather than a real
migration history.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from admissions_platform.models import Base


@pytest.fixture
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)
    session: Session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
