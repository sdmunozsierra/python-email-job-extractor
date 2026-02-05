"""
Analytics module for the email opportunity pipeline.

Provides detailed metrics, summaries, and insights about email processing,
filtering decisions, and extraction results.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import EmailMessage, FilterDecision, FilterOutcome


@dataclass
class FilterStats:
    """Statistics for a single filter."""
    name: str
    total_evaluated: int = 0
    passed: int = 0
    failed: int = 0
    reason_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def pass_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.passed / self.total_evaluated * 100

    @property
    def fail_rate(self) -> float:
        if self.total_evaluated == 0:
            return 0.0
        return self.failed / self.total_evaluated * 100


@dataclass
class DomainStats:
    """Statistics for email domains."""
    domain: str
    total: int = 0
    passed: int = 0
    failed: int = 0

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total * 100


@dataclass
class PipelineAnalytics:
    """
    Comprehensive analytics for the email processing pipeline.
    
    Tracks metrics across all stages: fetching, filtering, and extraction.
    """
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Input metrics
    total_emails_fetched: int = 0
    emails_with_body: int = 0
    emails_metadata_only: int = 0
    
    # Filter metrics
    total_emails_filtered: int = 0
    emails_passed_filter: int = 0
    emails_failed_filter: int = 0
    filter_stats: Dict[str, FilterStats] = field(default_factory=dict)
    
    # Domain analysis
    domain_stats: Dict[str, DomainStats] = field(default_factory=dict)
    sender_pattern_stats: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Score distribution (for keyword filter)
    score_distribution: List[float] = field(default_factory=list)
    passed_scores: List[float] = field(default_factory=list)
    failed_scores: List[float] = field(default_factory=list)
    
    # Reason analysis
    pass_reasons: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    fail_reasons: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Time analysis
    emails_by_date: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    emails_by_hour: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    
    # Extraction metrics
    total_opportunities_extracted: int = 0
    opportunities_with_company: int = 0
    opportunities_with_role: int = 0
    opportunities_with_salary: int = 0
    opportunities_with_location: int = 0
    company_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    role_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # Label analysis (Gmail labels)
    label_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    label_pass_rates: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # (passed, total)

    def start(self) -> None:
        """Mark the start of pipeline processing."""
        self.start_time = datetime.now(timezone.utc)

    def finish(self) -> None:
        """Mark the end of pipeline processing."""
        self.end_time = datetime.now(timezone.utc)

    @property
    def processing_duration_seconds(self) -> float:
        """Get processing duration in seconds."""
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def filter_pass_rate(self) -> float:
        """Overall filter pass rate as percentage."""
        if self.total_emails_filtered == 0:
            return 0.0
        return self.emails_passed_filter / self.total_emails_filtered * 100

    @property
    def filter_fail_rate(self) -> float:
        """Overall filter fail rate as percentage."""
        if self.total_emails_filtered == 0:
            return 0.0
        return self.emails_failed_filter / self.total_emails_filtered * 100

    def record_email_fetch(self, email: EmailMessage) -> None:
        """Record metrics for a fetched email."""
        self.total_emails_fetched += 1
        
        if email.body_text or email.body_html:
            self.emails_with_body += 1
        else:
            self.emails_metadata_only += 1
        
        # Time analysis
        if email.internal_date:
            date_str = email.internal_date.strftime("%Y-%m-%d")
            self.emails_by_date[date_str] += 1
            self.emails_by_hour[email.internal_date.hour] += 1
        
        # Label analysis
        for label in email.labels:
            self.label_counts[label] += 1

    def record_filter_result(
        self, 
        email: EmailMessage, 
        outcome: FilterOutcome
    ) -> None:
        """Record metrics for a filter result."""
        self.total_emails_filtered += 1
        
        # Extract domain from sender
        domain = self._extract_domain(email.headers.from_)
        sender_pattern = self._extract_sender_pattern(email.headers.from_)
        
        # Update domain stats
        if domain:
            if domain not in self.domain_stats:
                self.domain_stats[domain] = DomainStats(domain=domain)
            self.domain_stats[domain].total += 1
        
        # Update sender pattern stats
        if sender_pattern:
            self.sender_pattern_stats[sender_pattern] += 1
        
        # Track label pass rates
        for label in email.labels:
            if label not in self.label_pass_rates:
                self.label_pass_rates[label] = (0, 0)
            passed, total = self.label_pass_rates[label]
            self.label_pass_rates[label] = (
                passed + (1 if outcome.passed else 0),
                total + 1
            )
        
        if outcome.passed:
            self.emails_passed_filter += 1
            if domain:
                self.domain_stats[domain].passed += 1
            for reason in outcome.reasons:
                self.pass_reasons[reason] += 1
        else:
            self.emails_failed_filter += 1
            if domain:
                self.domain_stats[domain].failed += 1
            for reason in outcome.reasons:
                self.fail_reasons[reason] += 1
        
        # Track individual filter stats
        for decision in outcome.decisions:
            if decision.filter_name not in self.filter_stats:
                self.filter_stats[decision.filter_name] = FilterStats(name=decision.filter_name)
            
            stats = self.filter_stats[decision.filter_name]
            stats.total_evaluated += 1
            
            if decision.passed:
                stats.passed += 1
            else:
                stats.failed += 1
            
            for reason in decision.reasons:
                stats.reason_counts[reason] += 1
                
                # Extract score if present
                score_match = re.search(r"score:\s*([-\d.]+)", reason)
                if score_match:
                    score = float(score_match.group(1))
                    self.score_distribution.append(score)
                    if decision.passed:
                        self.passed_scores.append(score)
                    else:
                        self.failed_scores.append(score)

    def record_extraction(self, opportunity: Dict[str, Any]) -> None:
        """Record metrics for an extracted opportunity."""
        self.total_opportunities_extracted += 1
        
        company = opportunity.get("company", {}) or {}
        if company.get("name"):
            self.opportunities_with_company += 1
            self.company_counts[company["name"]] += 1
        
        role = opportunity.get("role", {}) or {}
        if role.get("title"):
            self.opportunities_with_role += 1
            self.role_counts[role["title"]] += 1
        
        compensation = opportunity.get("compensation", {}) or {}
        if compensation.get("base_salary") or compensation.get("salary_range"):
            self.opportunities_with_salary += 1
        
        location = opportunity.get("location", {}) or {}
        if location.get("city") or location.get("state") or location.get("remote"):
            self.opportunities_with_location += 1

    def _extract_domain(self, from_header: str) -> str:
        """Extract domain from From header."""
        match = re.search(r"@([A-Z0-9.-]+\.[A-Z]{2,})", from_header, re.I)
        return match.group(1).lower() if match else ""

    def _extract_sender_pattern(self, from_header: str) -> str:
        """Extract sender pattern (local part category) from From header."""
        match = re.search(r"([A-Z0-9._%+-]+)@", from_header, re.I)
        if not match:
            return ""
        
        local_part = match.group(1).lower()
        
        # Categorize sender patterns
        patterns = {
            "noreply": r"^(no-?reply|do-?not-?reply)",
            "marketing": r"^(marketing|promo|promotions?|campaign)",
            "newsletter": r"^(newsletter|news|updates?)",
            "notifications": r"^(notification|alert|notify)",
            "info": r"^(info|contact|hello|hi)",
            "support": r"^(support|help|service)",
            "team": r"^team",
            "recruiting": r"^(recruit|talent|hiring|careers?|jobs?)",
            "billing": r"^(billing|invoice|payment|account)",
            "personal": r"^[a-z]+\.[a-z]+",  # firstname.lastname pattern
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, local_part):
                return pattern_name
        
        return "other"

    def to_dict(self) -> Dict[str, Any]:
        """Convert analytics to dictionary for JSON serialization."""
        return {
            "timing": {
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "duration_seconds": self.processing_duration_seconds,
            },
            "input_metrics": {
                "total_emails_fetched": self.total_emails_fetched,
                "emails_with_body": self.emails_with_body,
                "emails_metadata_only": self.emails_metadata_only,
            },
            "filter_metrics": {
                "total_filtered": self.total_emails_filtered,
                "passed": self.emails_passed_filter,
                "failed": self.emails_failed_filter,
                "pass_rate_percent": round(self.filter_pass_rate, 2),
                "fail_rate_percent": round(self.filter_fail_rate, 2),
            },
            "extraction_metrics": {
                "total_opportunities": self.total_opportunities_extracted,
                "with_company": self.opportunities_with_company,
                "with_role": self.opportunities_with_role,
                "with_salary": self.opportunities_with_salary,
                "with_location": self.opportunities_with_location,
            },
            "score_distribution": {
                "all_scores": {
                    "count": len(self.score_distribution),
                    "min": min(self.score_distribution) if self.score_distribution else 0,
                    "max": max(self.score_distribution) if self.score_distribution else 0,
                    "avg": sum(self.score_distribution) / len(self.score_distribution) if self.score_distribution else 0,
                },
                "passed_scores": {
                    "count": len(self.passed_scores),
                    "min": min(self.passed_scores) if self.passed_scores else 0,
                    "max": max(self.passed_scores) if self.passed_scores else 0,
                    "avg": sum(self.passed_scores) / len(self.passed_scores) if self.passed_scores else 0,
                },
                "failed_scores": {
                    "count": len(self.failed_scores),
                    "min": min(self.failed_scores) if self.failed_scores else 0,
                    "max": max(self.failed_scores) if self.failed_scores else 0,
                    "avg": sum(self.failed_scores) / len(self.failed_scores) if self.failed_scores else 0,
                },
            },
            "top_domains": dict(
                sorted(
                    [(d, s.total) for d, s in self.domain_stats.items()],
                    key=lambda x: x[1],
                    reverse=True
                )[:20]
            ),
            "top_pass_reasons": dict(
                sorted(self.pass_reasons.items(), key=lambda x: x[1], reverse=True)[:15]
            ),
            "top_fail_reasons": dict(
                sorted(self.fail_reasons.items(), key=lambda x: x[1], reverse=True)[:15]
            ),
            "sender_patterns": dict(self.sender_pattern_stats),
            "emails_by_date": dict(sorted(self.emails_by_date.items())),
            "label_stats": {
                label: {"passed": p, "total": t, "pass_rate": round(p/t*100, 1) if t > 0 else 0}
                for label, (p, t) in sorted(
                    self.label_pass_rates.items(),
                    key=lambda x: x[1][1],
                    reverse=True
                )[:15]
            },
        }


def generate_report(analytics: PipelineAnalytics) -> str:
    """
    Generate a human-readable analytics report.
    
    Args:
        analytics: PipelineAnalytics object with collected metrics
        
    Returns:
        Formatted string report
    """
    lines = []
    
    # Header
    lines.append("=" * 70)
    lines.append("           EMAIL OPPORTUNITY PIPELINE - ANALYTICS REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Timing
    if analytics.start_time:
        lines.append(f"Report Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Processing Time:  {analytics.processing_duration_seconds:.2f} seconds")
        lines.append("")
    
    # Executive Summary
    lines.append("-" * 70)
    lines.append("                         EXECUTIVE SUMMARY")
    lines.append("-" * 70)
    lines.append("")
    lines.append(f"  Total Emails Processed:     {analytics.total_emails_filtered:,}")
    lines.append(f"  Emails Passed Filter:       {analytics.emails_passed_filter:,} ({analytics.filter_pass_rate:.1f}%)")
    lines.append(f"  Emails Failed Filter:       {analytics.emails_failed_filter:,} ({analytics.filter_fail_rate:.1f}%)")
    lines.append(f"  Opportunities Extracted:    {analytics.total_opportunities_extracted:,}")
    lines.append("")
    
    # Filter Performance
    lines.append("-" * 70)
    lines.append("                        FILTER PERFORMANCE")
    lines.append("-" * 70)
    lines.append("")
    
    for filter_name, stats in analytics.filter_stats.items():
        lines.append(f"  {filter_name.upper()} Filter:")
        lines.append(f"    Evaluated: {stats.total_evaluated:,}")
        lines.append(f"    Passed:    {stats.passed:,} ({stats.pass_rate:.1f}%)")
        lines.append(f"    Failed:    {stats.failed:,} ({stats.fail_rate:.1f}%)")
        lines.append("")
    
    # Score Distribution
    if analytics.score_distribution:
        lines.append("-" * 70)
        lines.append("                       SCORE DISTRIBUTION")
        lines.append("-" * 70)
        lines.append("")
        
        all_scores = analytics.score_distribution
        passed = analytics.passed_scores
        failed = analytics.failed_scores
        
        lines.append(f"  Overall Scores:")
        lines.append(f"    Count:   {len(all_scores):,}")
        lines.append(f"    Min:     {min(all_scores):.1f}")
        lines.append(f"    Max:     {max(all_scores):.1f}")
        lines.append(f"    Average: {sum(all_scores)/len(all_scores):.1f}")
        lines.append("")
        
        if passed:
            lines.append(f"  Passed Emails:")
            lines.append(f"    Count:   {len(passed):,}")
            lines.append(f"    Min:     {min(passed):.1f}")
            lines.append(f"    Max:     {max(passed):.1f}")
            lines.append(f"    Average: {sum(passed)/len(passed):.1f}")
            lines.append("")
        
        if failed:
            lines.append(f"  Failed Emails:")
            lines.append(f"    Count:   {len(failed):,}")
            lines.append(f"    Min:     {min(failed):.1f}")
            lines.append(f"    Max:     {max(failed):.1f}")
            lines.append(f"    Average: {sum(failed)/len(failed):.1f}")
            lines.append("")
        
        # Score histogram
        lines.append("  Score Histogram:")
        buckets = defaultdict(int)
        for score in all_scores:
            bucket = int(score // 2) * 2  # 2-point buckets
            buckets[bucket] += 1
        
        max_count = max(buckets.values()) if buckets else 1
        for bucket in sorted(buckets.keys()):
            count = buckets[bucket]
            bar_len = int(count / max_count * 30)
            bar = "█" * bar_len
            lines.append(f"    {bucket:>4} to {bucket+2:<4}: {bar} ({count})")
        lines.append("")
    
    # Top Failure Reasons
    if analytics.fail_reasons:
        lines.append("-" * 70)
        lines.append("                     TOP FAILURE REASONS")
        lines.append("-" * 70)
        lines.append("")
        
        sorted_reasons = sorted(analytics.fail_reasons.items(), key=lambda x: x[1], reverse=True)
        for i, (reason, count) in enumerate(sorted_reasons[:10], 1):
            # Truncate long reasons
            display_reason = reason[:55] + "..." if len(reason) > 58 else reason
            pct = count / analytics.emails_failed_filter * 100 if analytics.emails_failed_filter > 0 else 0
            lines.append(f"  {i:2}. {display_reason}")
            lines.append(f"      Count: {count:,} ({pct:.1f}% of failures)")
        lines.append("")
    
    # Top Pass Reasons
    if analytics.pass_reasons:
        lines.append("-" * 70)
        lines.append("                      TOP PASS REASONS")
        lines.append("-" * 70)
        lines.append("")
        
        sorted_reasons = sorted(analytics.pass_reasons.items(), key=lambda x: x[1], reverse=True)
        for i, (reason, count) in enumerate(sorted_reasons[:10], 1):
            display_reason = reason[:55] + "..." if len(reason) > 58 else reason
            pct = count / analytics.emails_passed_filter * 100 if analytics.emails_passed_filter > 0 else 0
            lines.append(f"  {i:2}. {display_reason}")
            lines.append(f"      Count: {count:,} ({pct:.1f}% of passes)")
        lines.append("")
    
    # Domain Analysis
    if analytics.domain_stats:
        lines.append("-" * 70)
        lines.append("                       DOMAIN ANALYSIS")
        lines.append("-" * 70)
        lines.append("")
        
        # Top domains by volume
        sorted_domains = sorted(
            analytics.domain_stats.values(),
            key=lambda x: x.total,
            reverse=True
        )[:15]
        
        lines.append("  Top Domains by Volume:")
        lines.append("  " + "-" * 66)
        lines.append(f"  {'Domain':<35} {'Total':>8} {'Passed':>8} {'Rate':>10}")
        lines.append("  " + "-" * 66)
        
        for stats in sorted_domains:
            domain_display = stats.domain[:33] + ".." if len(stats.domain) > 35 else stats.domain
            lines.append(
                f"  {domain_display:<35} {stats.total:>8} {stats.passed:>8} {stats.pass_rate:>9.1f}%"
            )
        lines.append("")
        
        # Domains with highest pass rates (min 3 emails)
        high_pass_domains = [
            s for s in analytics.domain_stats.values()
            if s.total >= 3 and s.pass_rate > 50
        ]
        if high_pass_domains:
            high_pass_domains.sort(key=lambda x: x.pass_rate, reverse=True)
            lines.append("  High-Quality Domains (>50% pass rate, min 3 emails):")
            lines.append("  " + "-" * 66)
            for stats in high_pass_domains[:10]:
                domain_display = stats.domain[:33] + ".." if len(stats.domain) > 35 else stats.domain
                lines.append(
                    f"  {domain_display:<35} {stats.total:>8} {stats.passed:>8} {stats.pass_rate:>9.1f}%"
                )
            lines.append("")
    
    # Sender Pattern Analysis
    if analytics.sender_pattern_stats:
        lines.append("-" * 70)
        lines.append("                    SENDER PATTERN ANALYSIS")
        lines.append("-" * 70)
        lines.append("")
        
        sorted_patterns = sorted(
            analytics.sender_pattern_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        total = sum(analytics.sender_pattern_stats.values())
        lines.append(f"  {'Pattern':<20} {'Count':>10} {'Percentage':>12}")
        lines.append("  " + "-" * 44)
        
        for pattern, count in sorted_patterns:
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"  {pattern:<20} {count:>10} {pct:>11.1f}%")
        lines.append("")
    
    # Gmail Label Analysis
    if analytics.label_pass_rates:
        lines.append("-" * 70)
        lines.append("                     GMAIL LABEL ANALYSIS")
        lines.append("-" * 70)
        lines.append("")
        
        sorted_labels = sorted(
            analytics.label_pass_rates.items(),
            key=lambda x: x[1][1],
            reverse=True
        )[:15]
        
        lines.append(f"  {'Label':<30} {'Total':>8} {'Passed':>8} {'Rate':>10}")
        lines.append("  " + "-" * 58)
        
        for label, (passed, total) in sorted_labels:
            label_display = label[:28] + ".." if len(label) > 30 else label
            rate = passed / total * 100 if total > 0 else 0
            lines.append(f"  {label_display:<30} {total:>8} {passed:>8} {rate:>9.1f}%")
        lines.append("")
    
    # Time Analysis
    if analytics.emails_by_date:
        lines.append("-" * 70)
        lines.append("                       TIME ANALYSIS")
        lines.append("-" * 70)
        lines.append("")
        
        lines.append("  Emails by Date:")
        sorted_dates = sorted(analytics.emails_by_date.items())
        for date, count in sorted_dates[-14:]:  # Last 14 days
            bar_len = min(count, 40)
            bar = "█" * bar_len
            lines.append(f"    {date}: {bar} ({count})")
        lines.append("")
    
    if analytics.emails_by_hour:
        lines.append("  Emails by Hour (UTC):")
        max_count = max(analytics.emails_by_hour.values()) if analytics.emails_by_hour else 1
        for hour in range(24):
            count = analytics.emails_by_hour.get(hour, 0)
            bar_len = int(count / max_count * 25) if max_count > 0 else 0
            bar = "█" * bar_len
            lines.append(f"    {hour:02d}:00 {bar} ({count})")
        lines.append("")
    
    # Extraction Quality
    if analytics.total_opportunities_extracted > 0:
        lines.append("-" * 70)
        lines.append("                     EXTRACTION QUALITY")
        lines.append("-" * 70)
        lines.append("")
        
        total = analytics.total_opportunities_extracted
        lines.append(f"  Total Opportunities:    {total:,}")
        lines.append(f"  With Company Name:      {analytics.opportunities_with_company:,} ({analytics.opportunities_with_company/total*100:.1f}%)")
        lines.append(f"  With Role Title:        {analytics.opportunities_with_role:,} ({analytics.opportunities_with_role/total*100:.1f}%)")
        lines.append(f"  With Salary Info:       {analytics.opportunities_with_salary:,} ({analytics.opportunities_with_salary/total*100:.1f}%)")
        lines.append(f"  With Location:          {analytics.opportunities_with_location:,} ({analytics.opportunities_with_location/total*100:.1f}%)")
        lines.append("")
        
        if analytics.company_counts:
            lines.append("  Top Companies:")
            top_companies = sorted(analytics.company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for company, count in top_companies:
                company_display = company[:40] + "..." if len(company) > 43 else company
                lines.append(f"    - {company_display}: {count}")
            lines.append("")
        
        if analytics.role_counts:
            lines.append("  Top Roles:")
            top_roles = sorted(analytics.role_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for role, count in top_roles:
                role_display = role[:40] + "..." if len(role) > 43 else role
                lines.append(f"    - {role_display}: {count}")
            lines.append("")
    
    # Insights & Recommendations
    lines.append("-" * 70)
    lines.append("                    INSIGHTS & RECOMMENDATIONS")
    lines.append("-" * 70)
    lines.append("")
    
    insights = _generate_insights(analytics)
    for i, insight in enumerate(insights, 1):
        lines.append(f"  {i}. {insight}")
    lines.append("")
    
    # Footer
    lines.append("=" * 70)
    lines.append("                         END OF REPORT")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def _generate_insights(analytics: PipelineAnalytics) -> List[str]:
    """Generate actionable insights based on analytics."""
    insights = []
    
    # Pass rate insights
    if analytics.filter_pass_rate < 5:
        insights.append(
            f"Very low pass rate ({analytics.filter_pass_rate:.1f}%). "
            "Consider reviewing filter rules - they may be too strict."
        )
    elif analytics.filter_pass_rate > 50:
        insights.append(
            f"High pass rate ({analytics.filter_pass_rate:.1f}%). "
            "Consider tightening filters to reduce noise."
        )
    else:
        insights.append(
            f"Pass rate of {analytics.filter_pass_rate:.1f}% is within normal range."
        )
    
    # Score distribution insights
    if analytics.failed_scores and analytics.passed_scores:
        avg_failed = sum(analytics.failed_scores) / len(analytics.failed_scores)
        avg_passed = sum(analytics.passed_scores) / len(analytics.passed_scores)
        
        if avg_passed - avg_failed < 2:
            insights.append(
                "Score gap between passed and failed emails is small. "
                "Consider adding more distinguishing signals."
            )
    
    # Domain insights
    if analytics.domain_stats:
        high_volume_fails = [
            s for s in analytics.domain_stats.values()
            if s.total >= 5 and s.pass_rate == 0
        ]
        if high_volume_fails:
            domains = ", ".join(s.domain for s in high_volume_fails[:3])
            insights.append(
                f"Domains with high volume but 0% pass rate: {domains}. "
                "Consider adding to denylist."
            )
        
        high_quality_domains = [
            s for s in analytics.domain_stats.values()
            if s.total >= 3 and s.pass_rate >= 80
        ]
        if high_quality_domains:
            domains = ", ".join(s.domain for s in high_quality_domains[:3])
            insights.append(
                f"High-quality domains (≥80% pass rate): {domains}. "
                "These are likely job-related sources."
            )
    
    # Sender pattern insights
    if analytics.sender_pattern_stats:
        total = sum(analytics.sender_pattern_stats.values())
        noreply_count = analytics.sender_pattern_stats.get("noreply", 0)
        marketing_count = analytics.sender_pattern_stats.get("marketing", 0)
        recruiting_count = analytics.sender_pattern_stats.get("recruiting", 0)
        
        if recruiting_count / total > 0.1 if total > 0 else False:
            insights.append(
                f"Good signal: {recruiting_count} emails ({recruiting_count/total*100:.1f}%) "
                "from recruiting-pattern senders."
            )
        
        promo_pct = (noreply_count + marketing_count) / total * 100 if total > 0 else 0
        if promo_pct > 50:
            insights.append(
                f"High proportion ({promo_pct:.1f}%) of noreply/marketing senders. "
                "Many may be promotional emails."
            )
    
    # Extraction quality insights
    if analytics.total_opportunities_extracted > 0:
        total = analytics.total_opportunities_extracted
        
        if analytics.opportunities_with_company / total < 0.5:
            insights.append(
                "Less than 50% of opportunities have company names extracted. "
                "Consider improving extraction rules."
            )
        
        if analytics.opportunities_with_salary / total < 0.1:
            insights.append(
                "Very few opportunities have salary information. "
                "This is normal - most job emails don't include compensation."
            )
    
    # Time-based insights
    if analytics.emails_by_hour:
        peak_hour = max(analytics.emails_by_hour.items(), key=lambda x: x[1])[0]
        insights.append(
            f"Peak email reception time: {peak_hour:02d}:00 UTC. "
            "Schedule pipeline runs after peak hours for best coverage."
        )
    
    if not insights:
        insights.append("No specific recommendations at this time.")
    
    return insights


def save_analytics(analytics: PipelineAnalytics, path: Path) -> None:
    """Save analytics to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(analytics.to_dict(), f, indent=2, default=str)


def save_report(analytics: PipelineAnalytics, path: Path) -> None:
    """Save human-readable report to text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    report = generate_report(analytics)
    path.write_text(report, encoding="utf-8")
