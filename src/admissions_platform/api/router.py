"""Admissions-review API routes, mounted onto the shared FastAPI app
(student_journey/api/main.py) under the /admissions prefix — one running
process, one port, one set of CORS/rate-limit/Prometheus middleware,
rather than a second standalone app.

Just a health check for now (Phase 1: foundation) — upload/extraction/
validation/decision endpoints are added in later phases as each pipeline
stage is built.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}
