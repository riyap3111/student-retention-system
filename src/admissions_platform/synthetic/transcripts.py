"""Generates synthetic student transcripts — both the structured ground
truth (for testing extraction accuracy) and a rendered PDF in one of
several distinct layouts, standing in for "various different transcript
formats" from different institutions. No real student data anywhere.

Course codes/names are drawn from a small fixed pool shared with the mock
course catalog (catalog/mock_source.py, built in a later phase) so the two
line up for course-matching once that phase exists.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from fpdf import FPDF
from fpdf.enums import XPos, YPos

# "W" (withdrawal) carries no grade points and is excluded from GPA math
# below, matching the real-world convention most registrars use.
GRADE_POINTS = {
    "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "D": 1.0, "F": 0.0, "W": 0.0,
}
GPA_EXEMPT_GRADES = {"W"}

COURSE_POOL = [
    ("CS101", "Introduction to Programming", 3),
    ("CS201", "Data Structures", 3),
    ("MATH101", "Calculus I", 4),
    ("MATH201", "Calculus II", 4),
    ("MATH210", "Linear Algebra", 3),
    ("ENG101", "English Composition", 3),
    ("BIO101", "Introduction to Biology", 4),
    ("CHEM101", "General Chemistry", 4),
    ("PHYS101", "Physics I", 4),
    ("HIST101", "World History", 3),
    ("ECON101", "Principles of Economics", 3),
    ("STAT201", "Introduction to Statistics", 3),
]

INSTITUTIONS = ["Meridian Community College", "Lakeside Valley College", "Northbrook Technical Institute"]

FIRST_NAMES = ["Jordan", "Avery", "Taylor", "Morgan", "Riley", "Casey", "Sam", "Dakota"]
LAST_NAMES = ["Nguyen", "Garcia", "Patel", "Kim", "Brown", "Okafor", "Rossi", "Chen"]


@dataclass
class SyntheticCourse:
    code: str
    name: str
    credits: float
    grade: str
    term: str


@dataclass
class SyntheticTranscript:
    student_name: str
    institution_name: str
    courses: list[SyntheticCourse] = field(default_factory=list)

    @property
    def cumulative_gpa(self) -> float:
        gpa_courses = [c for c in self.courses if c.grade not in GPA_EXEMPT_GRADES]
        total_points = sum(GRADE_POINTS[c.grade] * c.credits for c in gpa_courses)
        total_credits = sum(c.credits for c in gpa_courses)
        return round(total_points / total_credits, 2) if total_credits else 0.0

    @property
    def withdrawal_count(self) -> int:
        return sum(1 for c in self.courses if c.grade == "W")


def generate_synthetic_transcript(
    rng: random.Random, n_terms: int = 3, courses_per_term: int = 4
) -> SyntheticTranscript:
    student_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
    institution_name = rng.choice(INSTITUTIONS)
    courses: list[SyntheticCourse] = []

    for term_index in range(1, n_terms + 1):
        term_label = f"Fall {2022 + term_index}" if term_index % 2 else f"Spring {2023 + term_index}"
        chosen = rng.sample(COURSE_POOL, k=min(courses_per_term, len(COURSE_POOL)))
        for code, name, credits in chosen:
            grade = rng.choices(
                list(GRADE_POINTS), weights=[25, 15, 15, 20, 10, 5, 5, 3, 2, 3]
            )[0]
            courses.append(
                SyntheticCourse(code=code, name=name, credits=float(credits), grade=grade, term=term_label)
            )

    return SyntheticTranscript(student_name=student_name, institution_name=institution_name, courses=courses)


FormatStyle = Literal["standard", "narrative", "compact"]


def render_transcript_pdf(transcript: SyntheticTranscript, format_style: FormatStyle = "standard") -> bytes:
    """Renders the same underlying data in one of three visually distinct
    layouts, so extraction can be tested against more than one transcript
    "format" without needing real institutional samples."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    if format_style == "standard":
        _render_standard(pdf, transcript)
    elif format_style == "narrative":
        _render_narrative(pdf, transcript)
    elif format_style == "compact":
        _render_compact(pdf, transcript)
    else:
        raise ValueError(f"Unknown format_style: {format_style}")

    return bytes(pdf.output())


def _render_standard(pdf: FPDF, t: SyntheticTranscript) -> None:
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, t.institution_name, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 8, "OFFICIAL ACADEMIC TRANSCRIPT", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    pdf.cell(0, 8, f"Student: {t.student_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    terms = sorted({c.term for c in t.courses})
    for term in terms:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, term, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(30, 6, "Course")
        pdf.cell(80, 6, "Title")
        pdf.cell(20, 6, "Credits")
        pdf.cell(20, 6, "Grade", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        for c in t.courses:
            if c.term != term:
                continue
            pdf.cell(30, 6, c.code)
            pdf.cell(80, 6, c.name)
            pdf.cell(20, 6, str(c.credits))
            pdf.cell(20, 6, c.grade, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Cumulative GPA: {t.cumulative_gpa}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _render_narrative(pdf: FPDF, t: SyntheticTranscript) -> None:
    """A second, deliberately different layout: prose paragraphs per term
    instead of a table, with the institution name at the bottom like some
    real community-college transcripts do."""
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"Transcript of Record - {t.student_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    terms = sorted({c.term for c in t.courses})
    for term in terms:
        term_courses = [c for c in t.courses if c.term == term]
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, f"Term: {term}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 10)
        line = "; ".join(f"{c.code} {c.name} ({c.credits} cr) - grade {c.grade}" for c in term_courses)
        pdf.multi_cell(0, 6, line)
        pdf.ln(1)

    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Cumulative GPA as of this record: {t.cumulative_gpa}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 6, f"Issued by {t.institution_name}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _render_compact(pdf: FPDF, t: SyntheticTranscript) -> None:
    """A third layout: everything in one dense table, no per-term grouping
    — closer to some registrar export formats."""
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, f"{t.institution_name} - Transcript", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Name: {t.student_name}  |  GPA: {t.cumulative_gpa}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(25, 5, "Term")
    pdf.cell(25, 5, "Code")
    pdf.cell(90, 5, "Course")
    pdf.cell(15, 5, "Cr")
    pdf.cell(15, 5, "Grd", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    for c in t.courses:
        pdf.cell(25, 5, c.term)
        pdf.cell(25, 5, c.code)
        pdf.cell(90, 5, c.name)
        pdf.cell(15, 5, str(c.credits))
        pdf.cell(15, 5, c.grade, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
