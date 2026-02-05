"""
Resume Tailoring module.

Takes match analysis insights and produces tailored resumes using the
resume-builder subtree package, along with a detailed report of every
change made (experience emphasis, skill highlighting, certification
selection).
"""

from .adapter import ResumeAdapter, adapt_resume_to_builder_schema
from .engine import TailoringEngine, tailor_resume
from .models import (
    TailoredResume,
    TailoringChange,
    TailoringReport,
    ChangeCategory,
)
from .report import render_tailoring_report, render_tailoring_summary

__all__ = [
    # Adapter
    "ResumeAdapter",
    "adapt_resume_to_builder_schema",
    # Engine
    "TailoringEngine",
    "tailor_resume",
    # Models
    "TailoredResume",
    "TailoringChange",
    "TailoringReport",
    "ChangeCategory",
    # Reporting
    "render_tailoring_report",
    "render_tailoring_summary",
]
