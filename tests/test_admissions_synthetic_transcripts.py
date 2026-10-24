"""Tests for the synthetic transcript generator: GPA math, withdrawal
counting, and that all three layout styles actually render valid PDFs."""
import random

import pytest

from admissions_platform.synthetic.transcripts import (
    FormatStyle,
    SyntheticCourse,
    SyntheticTranscript,
    generate_synthetic_transcript,
    render_transcript_pdf,
)


def test_cumulative_gpa_excludes_withdrawals():
    t = SyntheticTranscript(
        student_name="Jane Doe",
        institution_name="Test College",
        courses=[
            SyntheticCourse(code="CS101", name="Intro", credits=3.0, grade="A", term="Fall 2024"),
            SyntheticCourse(code="MATH101", name="Calc I", credits=4.0, grade="B", term="Fall 2024"),
            SyntheticCourse(code="ENG101", name="Comp", credits=3.0, grade="W", term="Fall 2024"),
        ],
    )
    # (4.0*3 + 3.0*4) / (3+4) = 24/7 = 3.43 -- the withdrawn course contributes nothing.
    assert t.cumulative_gpa == pytest.approx(3.43, abs=0.01)
    assert t.withdrawal_count == 1


def test_cumulative_gpa_is_zero_with_no_courses():
    t = SyntheticTranscript(student_name="Jane Doe", institution_name="Test College", courses=[])
    assert t.cumulative_gpa == 0.0
    assert t.withdrawal_count == 0


def test_generate_synthetic_transcript_is_deterministic_for_a_given_seed():
    t1 = generate_synthetic_transcript(random.Random(42))
    t2 = generate_synthetic_transcript(random.Random(42))
    assert t1.student_name == t2.student_name
    assert t1.cumulative_gpa == t2.cumulative_gpa
    assert len(t1.courses) == len(t2.courses)


def test_generate_synthetic_transcript_produces_courses_across_terms():
    t = generate_synthetic_transcript(random.Random(1), n_terms=3, courses_per_term=4)
    terms = {c.term for c in t.courses}
    assert len(terms) == 3
    assert len(t.courses) == 12


@pytest.mark.parametrize("format_style", ["standard", "narrative", "compact"])
def test_render_transcript_pdf_produces_a_valid_pdf_for_every_format(format_style: FormatStyle):
    t = generate_synthetic_transcript(random.Random(7))
    pdf_bytes = render_transcript_pdf(t, format_style=format_style)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500  # not an empty/near-empty document


def test_render_transcript_pdf_rejects_unknown_format():
    t = generate_synthetic_transcript(random.Random(7))
    with pytest.raises(ValueError):
        render_transcript_pdf(t, format_style="not-a-real-format")  # type: ignore[arg-type]
