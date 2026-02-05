"""
Job Analysis and Resume Matching module.

Provides LLM-based analysis of job opportunities against resumes,
generating match scores, insights, and recommendations.
"""

from .models import (
    Resume,
    MatchResult,
    SkillMatch,
    ExperienceMatch,
    MatchInsights,
    ResumeTailoring,
    ApplicationStrategy,
    CategoryScore,
)
from .resume_parser import ResumeParser, parse_resume_file
from .analyzer import JobAnalyzer, analyze_job
from .matcher import ResumeMatcher, match_resume_to_job
from .report import render_match_markdown, render_match_summary

__all__ = [
    # Models
    "Resume",
    "MatchResult",
    "SkillMatch",
    "ExperienceMatch",
    "MatchInsights",
    "ResumeTailoring",
    "ApplicationStrategy",
    "CategoryScore",
    # Resume parsing
    "ResumeParser",
    "parse_resume_file",
    # Analysis
    "JobAnalyzer",
    "analyze_job",
    # Matching
    "ResumeMatcher",
    "match_resume_to_job",
    # Reporting
    "render_match_markdown",
    "render_match_summary",
]
