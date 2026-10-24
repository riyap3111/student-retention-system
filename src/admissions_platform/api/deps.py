"""FastAPI dependencies for the admissions routes.

A real request-scoped SQLAlchemy Session (one per request, closed after)
bound to the shared engine (student_journey.db.get_engine()) - admissions
tests override `get_db_session` with a disposable per-test database via
app.dependency_overrides, the same mechanism used to swap in a
FakeLLMClient for `get_llm_client` so no test ever makes a real network
call to Gemini.
"""
from typing import Iterator

from fastapi import HTTPException
from sqlalchemy.orm import Session, sessionmaker

from admissions_platform.llm.client import LLMClient
from admissions_platform.llm.client import get_llm_client as _get_llm_client
from student_journey.db import get_engine

_SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    session = _SessionFactory()
    try:
        yield session
    finally:
        session.close()


def get_llm_client() -> LLMClient:
    # Mirrors student_journey.api.main.get_model_bundle's 503-when-not-ready
    # pattern: a missing GEMINI_API_KEY is an expected local-dev/deployment
    # state, not a server bug, so it shouldn't surface as a raw 500.
    try:
        return _get_llm_client()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
