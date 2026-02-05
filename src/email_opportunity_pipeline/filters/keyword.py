from __future__ import annotations

import re
from typing import List

from ..models import EmailMessage, FilterDecision
from .base import EmailFilter
from .rules import FilterRules


def _matches_any(patterns: List[str], text: str) -> List[str]:
    hits: List[str] = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.I):
            hits.append(pattern)
    return hits


def _extract_email_address(from_header: str) -> str:
    match = re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", from_header, re.I)
    return match.group(1).lower() if match else ""


def _domain_of(email_addr: str) -> str:
    if "@" not in email_addr:
        return ""
    return email_addr.split("@", 1)[1].lower()


class KeywordFilter(EmailFilter):
    name = "keyword"

    def __init__(self, rules: FilterRules | None = None) -> None:
        self.rules = rules or FilterRules.default()

    def evaluate(self, email: EmailMessage) -> FilterDecision:
        from_header = email.headers.from_
        subject = email.headers.subject or ""
        snippet = email.snippet or ""
        body = email.body_text or ""

        text_raw = f"{subject}\n{snippet}\n{body}".strip()
        text = text_raw.lower()

        email_addr = _extract_email_address(from_header)
        domain = _domain_of(email_addr)

        if domain and domain in self.rules.non_job_domains:
            return FilterDecision(
                filter_name=self.name,
                passed=False,
                reasons=[f"non-job domain denylist: {domain}"],
            )

        reasons: List[str] = []
        strong_hits = _matches_any(self.rules.strong_job_signal_patterns, text)
        if strong_hits:
            reasons.append("strong job signal")

        edu_hits = _matches_any(self.rules.edu_negative_patterns, text)
        if edu_hits and not strong_hits:
            return FilterDecision(
                filter_name=self.name,
                passed=False,
                reasons=["education/admissions pattern"],
            )

        if domain and domain in self.rules.job_source_domains:
            reasons.append(f"job source domain: {domain}")

        role_hits = _matches_any(self.rules.role_title_patterns, text)
        if role_hits:
            reasons.append("role/title mentioned")

        kw_hits: List[str] = []
        for keyword in self.rules.job_keywords:
            if keyword in text:
                kw_hits.append(keyword)

        if "schedule" in text:
            if _matches_any(self.rules.interview_context_patterns, text):
                kw_hits.append("schedule(interview-context)")

        if re.search(r"\boa\b", text, flags=re.I):
            if _matches_any(self.rules.oa_assessment_patterns, text):
                kw_hits.append("oa(assessment-context)")

        if kw_hits:
            uniq = sorted(set(kw_hits))
            reasons.append(
                "keyword hits: "
                + ", ".join(uniq[:8])
                + ("..." if len(uniq) > 8 else "")
            )

        promo_hits = _matches_any(self.rules.promo_negative_patterns, text)
        if promo_hits and not reasons:
            return FilterDecision(
                filter_name=self.name,
                passed=False,
                reasons=["promo/ecommerce/billing pattern"],
            )

        if not reasons:
            return FilterDecision(
                filter_name=self.name,
                passed=False,
                reasons=["no positive job signals"],
            )

        return FilterDecision(
            filter_name=self.name,
            passed=True,
            reasons=reasons,
        )
