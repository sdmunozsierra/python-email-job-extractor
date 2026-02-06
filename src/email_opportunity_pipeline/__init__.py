"""Email Opportunity Pipeline -- fetch, filter, and normalize email job opportunities.

This package provides a CLI (``email-pipeline``) and a Python API for:

1. **Fetching** emails from providers (Gmail, etc.)
2. **Filtering** messages through rule-based and LLM pipelines
3. **Extracting** structured job opportunities from emails
4. **Rendering** Markdown reports with YAML frontmatter
5. **Analyzing** job requirements with LLM
6. **Matching** resumes against job opportunities
7. **Tailoring** resumes per job using the vendor ``resume-builder`` package
8. **Replying** to recruiters with tailored, LLM-composed emails
9. **Correlating** opportunities with emails, resumes, and replies in a unified view

Quick start (Python API)::

    from email_opportunity_pipeline.matching import Resume, ResumeMatcher
    from email_opportunity_pipeline.tailoring import TailoringEngine
    from email_opportunity_pipeline.reply import ReplyComposer, GmailSender
    from email_opportunity_pipeline.correlation import OpportunityCorrelator

See ``docs/`` for full documentation.
"""

__all__ = [
    "__version__",
    "PipelineAnalytics",
    "generate_report",
]

__version__ = "0.1.0"

from .analytics import PipelineAnalytics, generate_report
