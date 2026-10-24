"""Paths specific to the admissions-review feature set.

The database itself is NOT configured here — admissions_platform shares
one physical database (and `get_engine()`) with student_journey.db now
that both packages live in the same project; see db/migrations/env.py and
README for how the two feature sets' tables coexist with no naming
collisions.
"""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
HANDBOOKS_DIR = DATA_DIR / "handbooks"
CATALOG_FIXTURES_DIR = DATA_DIR / "catalog_fixtures"

STORAGE_DIR = PROJECT_ROOT / "storage"  # local-disk document storage (see storage/local.py)

RANDOM_SEED = 42

for _dir in (DATA_DIR, HANDBOOKS_DIR, CATALOG_FIXTURES_DIR, STORAGE_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
