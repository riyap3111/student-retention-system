"""Loads the fixed, clearly-fictional sample admissions handbook used
throughout this project (data/handbooks/sample_admissions_handbook.md).

Unlike transcripts, the handbook isn't randomly generated — it's one
hand-authored policy document the rules-extraction pipeline parses. Kept in
this package anyway since it's the other half of this project's synthetic
("no real institution's real data") fixtures.
"""
from admissions_platform.config import HANDBOOKS_DIR

SAMPLE_HANDBOOK_PATH = HANDBOOKS_DIR / "sample_admissions_handbook.md"


def load_sample_handbook_text() -> str:
    return SAMPLE_HANDBOOK_PATH.read_text()
