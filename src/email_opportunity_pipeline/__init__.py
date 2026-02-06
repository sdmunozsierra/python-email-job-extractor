"""Email Opportunity Pipeline -- fetch, filter, and normalize email job opportunities.

This package provides a CLI (``email-pipeline``) and a Python API for:

1. **Fetching** emails from providers (Gmail, etc.)
2. **Filtering** messages through rule-based and LLM pipelines
3. **Extracting** structured job opportunities from emails
4. **Rendering** Markdown reports with YAML frontmatter
5. **Analyzing** job requirements with LLM
6. **Matching** resumes against job opportunities
7. **Tailoring** resumes per job using the vendor ``resume-builder`` package

Quick start (Python API)::

    from email_opportunity_pipeline.matching import Resume, ResumeMatcher
    from email_opportunity_pipeline.tailoring import TailoringEngine

See ``docs/`` for full documentation.
"""

__all__ = [
    "__version__",
    "PipelineAnalytics",
    "generate_report",
]

__version__ = "0.1.0"

from .analytics import PipelineAnalytics, generate_report
