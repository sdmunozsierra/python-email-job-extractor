"""
Job-opportunity correlation module.

Provides a unified view that links every pipeline artifact (email,
opportunity, match result, tailored resume, reply draft, reply result) for
each job opportunity.  Users can see the complete lifecycle of every
opportunity at a glance and generate rich Markdown reports.

Quick start (Python API)::

    from email_opportunity_pipeline.correlation import (
        OpportunityCorrelator,
        render_correlation_report,
    )

    correlator = OpportunityCorrelator()
    correlator.add_opportunities(opportunities)
    correlator.add_match_results(match_results)
    correlated = correlator.correlate()
    summary = correlator.build_summary(correlated)
    print(render_correlation_report(summary, correlated))

CLI::

    email-pipeline correlate --work-dir data --out-dir output --out correlation
"""

__all__ = [
    "CorrelatedOpportunity",
    "CorrelationSummary",
    "EmailSummary",
    "MatchSummary",
    "OpportunityCorrelator",
    "OpportunityStage",
    "ReplyOutcome",
    "ReplySummary",
    "TailoringSummary",
    "render_correlation_report",
    "render_correlation_summary",
    "render_opportunity_card",
]

from .correlator import OpportunityCorrelator
from .models import (
    CorrelatedOpportunity,
    CorrelationSummary,
    EmailSummary,
    MatchSummary,
    OpportunityStage,
    ReplyOutcome,
    ReplySummary,
    TailoringSummary,
)
from .report import (
    render_correlation_report,
    render_correlation_summary,
    render_opportunity_card,
)
