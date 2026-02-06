"""
Opportunity correlator engine.

Links all pipeline artifacts (emails, opportunities, match results, tailored
resumes, reply drafts, reply results) by their shared ``job_id`` /
``message_id`` key, producing a unified :class:`CorrelatedOpportunity` for
every job found across the provided data sources.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

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

if TYPE_CHECKING:
    from ..matching.models import MatchResult
    from ..models import EmailMessage
    from ..reply.models import EmailDraft, ReplyResult


class OpportunityCorrelator:
    """Build correlated views of job opportunities across pipeline artifacts.

    Usage::

        correlator = OpportunityCorrelator()
        correlator.add_messages(messages)
        correlator.add_opportunities(opportunities)
        correlator.add_match_results(match_results)
        correlator.add_tailoring_results(tailoring_results, tailored_dir)
        correlator.add_drafts(drafts)
        correlator.add_reply_results(reply_results)

        correlated = correlator.correlate()
        summary = correlator.build_summary(correlated, resume_name="Alex")
    """

    def __init__(self) -> None:
        # Internal stores keyed by job_id (message_id)
        self._emails: Dict[str, "EmailMessage"] = {}
        self._opportunities: Dict[str, Dict[str, Any]] = {}
        self._match_results: Dict[str, "MatchResult"] = {}
        self._tailoring: Dict[str, Dict[str, Any]] = {}
        self._tailored_dir: Optional[Path] = None
        self._drafts: Dict[str, "EmailDraft"] = {}
        self._reply_results: Dict[str, "ReplyResult"] = {}

    # ------------------------------------------------------------------
    # Data ingestion
    # ------------------------------------------------------------------

    def add_messages(self, messages: List["EmailMessage"]) -> None:
        """Register source email messages."""
        for msg in messages:
            if msg.message_id:
                self._emails[msg.message_id] = msg

    def add_opportunities(self, opportunities: List[Dict[str, Any]]) -> None:
        """Register extracted job opportunities."""
        for opp in opportunities:
            msg_id = _opp_job_id(opp)
            if msg_id:
                self._opportunities[msg_id] = opp

    def add_match_results(self, results: List["MatchResult"]) -> None:
        """Register resume-job match results."""
        for r in results:
            if r.job_id:
                self._match_results[r.job_id] = r

    def add_tailoring_results(
        self,
        results: List[Dict[str, Any]],
        tailored_dir: Optional[Path] = None,
    ) -> None:
        """Register tailoring results (from ``tailoring_results.json``).

        *results* should be a list of dicts with at least a ``report`` key
        containing the tailoring report dict (``job_id``, ``total_changes``,
        etc.) and optionally ``docx_path``.
        """
        self._tailored_dir = tailored_dir
        for item in results:
            report = item.get("report", {})
            job_id = report.get("job_id", "")
            if job_id:
                self._tailoring[job_id] = item

    def add_drafts(self, drafts: List["EmailDraft"]) -> None:
        """Register composed reply drafts."""
        for d in drafts:
            if d.job_id:
                self._drafts[d.job_id] = d

    def add_reply_results(self, results: List["ReplyResult"]) -> None:
        """Register reply send results."""
        for r in results:
            if r.draft.job_id:
                self._reply_results[r.draft.job_id] = r

    # ------------------------------------------------------------------
    # Correlation
    # ------------------------------------------------------------------

    def correlate(self) -> List[CorrelatedOpportunity]:
        """Build correlated opportunities from all registered artifacts.

        Returns a list of :class:`CorrelatedOpportunity` objects, one per
        unique ``job_id`` found across *any* data source, sorted by match
        score descending (unmatched opportunities come last).
        """
        # Collect all known job_ids across every data source
        all_ids: set[str] = set()
        all_ids.update(self._emails.keys())
        all_ids.update(self._opportunities.keys())
        all_ids.update(self._match_results.keys())
        all_ids.update(self._tailoring.keys())
        all_ids.update(self._drafts.keys())
        all_ids.update(self._reply_results.keys())

        correlated: List[CorrelatedOpportunity] = []
        for job_id in all_ids:
            correlated.append(self._build_one(job_id))

        # Sort: matched opportunities first (by score desc), then unmatched
        correlated.sort(
            key=lambda c: (
                c.match.overall_score if c.match else -1,
            ),
            reverse=True,
        )
        return correlated

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def build_summary(
        self,
        correlated: List[CorrelatedOpportunity],
        resume_name: Optional[str] = None,
        resume_file: Optional[str] = None,
    ) -> CorrelationSummary:
        """Compute aggregate statistics from a list of correlated opportunities."""
        summary = CorrelationSummary(
            total_opportunities=len(correlated),
            resume_name=resume_name,
            resume_file=resume_file,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        stage_counts: Dict[str, int] = defaultdict(int)
        grade_counts: Dict[str, int] = defaultdict(int)
        rec_counts: Dict[str, int] = defaultdict(int)
        company_counts: Dict[str, int] = defaultdict(int)
        scores: List[float] = []

        for c in correlated:
            stage_counts[c.stage.value] += 1

            if c.pipeline_complete:
                summary.pipeline_complete_count += 1

            if c.company:
                company_counts[c.company] += 1

            # Match stats
            if c.match:
                summary.matched_count += 1
                scores.append(c.match.overall_score)
                if c.match.match_grade:
                    grade_counts[c.match.match_grade] += 1
                if c.match.recommendation:
                    rec_counts[c.match.recommendation] += 1

            # Tailoring stats
            if c.tailoring:
                summary.tailored_count += 1
                summary.total_tailoring_changes += c.tailoring.total_changes
                if c.tailoring.docx_path:
                    summary.docx_generated += 1

            # Reply stats
            if c.reply:
                if c.reply.status == ReplyOutcome.DRAFTED:
                    summary.replies_drafted += 1
                elif c.reply.status == ReplyOutcome.SENT:
                    summary.replies_sent += 1
                elif c.reply.status == ReplyOutcome.FAILED:
                    summary.replies_failed += 1
                elif c.reply.status == ReplyOutcome.DRY_RUN:
                    summary.replies_dry_run += 1

        summary.by_stage = dict(stage_counts)
        summary.by_grade = dict(grade_counts)
        summary.by_recommendation = dict(rec_counts)

        if scores:
            summary.avg_match_score = sum(scores) / len(scores)
            summary.max_match_score = max(scores)
            summary.min_match_score = min(scores)

        # Top companies
        sorted_companies = sorted(
            company_counts.items(), key=lambda x: x[1], reverse=True
        )
        summary.top_companies = [
            {"company": name, "count": count}
            for name, count in sorted_companies[:10]
        ]

        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_one(self, job_id: str) -> CorrelatedOpportunity:
        """Assemble a single correlated opportunity from all data sources."""
        email_msg = self._emails.get(job_id)
        opp = self._opportunities.get(job_id)
        match_result = self._match_results.get(job_id)
        tailoring_data = self._tailoring.get(job_id)
        draft = self._drafts.get(job_id)
        reply_result = self._reply_results.get(job_id)

        # --- identity ---
        job_title = ""
        company = ""
        recruiter_name = None
        recruiter_email = None
        locations: List[str] = []
        remote: Optional[bool] = None
        hybrid: Optional[bool] = None

        if opp:
            job_title = opp.get("job_title", "") or ""
            company = opp.get("company", "") or ""
            recruiter_name = opp.get("recruiter_name")
            recruiter_email = opp.get("recruiter_email")
            locations = opp.get("locations", []) or []
            remote = opp.get("remote")
            hybrid = opp.get("hybrid")

        # --- email summary ---
        email_summary: Optional[EmailSummary] = None
        email_received_at: Optional[str] = None
        if email_msg:
            email_summary = EmailSummary(
                message_id=email_msg.message_id,
                thread_id=email_msg.thread_id,
                subject=email_msg.headers.subject,
                from_address=email_msg.headers.from_,
                date=email_msg.headers.date,
                snippet=email_msg.snippet[:200] if email_msg.snippet else "",
                labels=list(email_msg.labels),
                has_attachments=len(email_msg.attachments) > 0,
            )
            if email_msg.internal_date:
                email_received_at = email_msg.internal_date.isoformat()

        # --- match summary ---
        match_summary: Optional[MatchSummary] = None
        matched_at: Optional[str] = None
        if match_result:
            match_summary = MatchSummary(
                overall_score=match_result.overall_score,
                match_grade=match_result.match_grade,
                recommendation=match_result.recommendation,
                skills_score=match_result.skills_match.score,
                experience_score=match_result.experience_match.score,
                education_score=match_result.education_score.score,
                location_score=match_result.location_score.score,
                culture_fit_score=match_result.culture_fit_score.score,
                mandatory_skills_met=match_result.skills_match.mandatory_met,
                mandatory_skills_total=match_result.skills_match.mandatory_total,
                preferred_skills_met=match_result.skills_match.preferred_met,
                preferred_skills_total=match_result.skills_match.preferred_total,
                top_strengths=list(match_result.insights.strengths[:3]),
                top_concerns=list(match_result.insights.concerns[:3]),
                missing_skills=list(match_result.skills_match.missing_mandatory[:5]),
            )
            if match_result.timestamp:
                matched_at = match_result.timestamp.isoformat()

        # --- tailoring summary ---
        tailoring_summary: Optional[TailoringSummary] = None
        tailored_at: Optional[str] = None
        if tailoring_data:
            report = tailoring_data.get("report", {})
            tailoring_summary = TailoringSummary(
                total_changes=report.get("total_changes", 0),
                changes_by_category=report.get("changes_by_category", {}),
                docx_path=tailoring_data.get("docx_path"),
                resume_json_path=None,  # can be resolved from tailored_dir
            )
            ts = report.get("timestamp")
            if ts:
                tailored_at = ts

        # --- reply summary ---
        reply_summary: Optional[ReplySummary] = None
        replied_at: Optional[str] = None
        if draft or reply_result:
            d = reply_result.draft if reply_result else draft
            body_preview = (d.body_text[:200] + "...") if d and len(d.body_text) > 200 else (d.body_text if d else "")
            status = ReplyOutcome.NOT_STARTED
            gmail_id = None
            error = None

            if reply_result:
                from ..reply.models import ReplyStatus

                status_map = {
                    ReplyStatus.DRAFT: ReplyOutcome.DRAFTED,
                    ReplyStatus.DRY_RUN: ReplyOutcome.DRY_RUN,
                    ReplyStatus.SENT: ReplyOutcome.SENT,
                    ReplyStatus.FAILED: ReplyOutcome.FAILED,
                }
                status = status_map.get(reply_result.status, ReplyOutcome.DRAFTED)
                gmail_id = reply_result.gmail_message_id
                error = reply_result.error
                if reply_result.timestamp:
                    replied_at = reply_result.timestamp.isoformat()
            elif draft:
                status = ReplyOutcome.DRAFTED

            reply_summary = ReplySummary(
                to=d.to if d else "",
                subject=d.subject if d else "",
                body_preview=body_preview,
                has_attachments=bool(d.attachment_paths) if d else False,
                attachment_count=len(d.attachment_paths) if d else 0,
                status=status,
                gmail_message_id=gmail_id,
                error=error,
                sent_at=replied_at,
            )

        # --- determine stage ---
        stage = self._determine_stage(
            email_msg, opp, match_result, tailoring_data, draft, reply_result
        )

        # --- pipeline complete? ---
        pipeline_complete = (
            reply_result is not None and reply_summary is not None
            and reply_summary.status in (ReplyOutcome.SENT, ReplyOutcome.DRY_RUN)
        )

        return CorrelatedOpportunity(
            job_id=job_id,
            job_title=job_title,
            company=company,
            recruiter_name=recruiter_name,
            recruiter_email=recruiter_email,
            stage=stage,
            pipeline_complete=pipeline_complete,
            locations=locations,
            remote=remote,
            hybrid=hybrid,
            email=email_summary,
            opportunity=opp,
            match=match_summary,
            tailoring=tailoring_summary,
            reply=reply_summary,
            email_received_at=email_received_at,
            matched_at=matched_at,
            tailored_at=tailored_at,
            replied_at=replied_at,
        )

    @staticmethod
    def _determine_stage(
        email: Optional[Any],
        opp: Optional[Dict],
        match: Optional[Any],
        tailoring: Optional[Dict],
        draft: Optional[Any],
        reply: Optional[Any],
    ) -> OpportunityStage:
        """Determine the furthest pipeline stage reached."""
        if reply is not None:
            return OpportunityStage.REPLIED
        if draft is not None:
            return OpportunityStage.COMPOSED
        if tailoring is not None:
            return OpportunityStage.TAILORED
        if match is not None:
            return OpportunityStage.MATCHED
        if opp is not None:
            return OpportunityStage.EXTRACTED
        if email is not None:
            return OpportunityStage.FETCHED
        return OpportunityStage.FETCHED


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _opp_job_id(opp: Dict[str, Any]) -> str:
    """Extract the job_id (message_id) from an opportunity dict."""
    source = opp.get("source_email", {})
    if isinstance(source, dict):
        return source.get("message_id", "")
    return ""
