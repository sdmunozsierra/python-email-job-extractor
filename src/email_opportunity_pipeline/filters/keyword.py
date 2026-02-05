from __future__ import annotations

import re
from typing import List, Tuple

from ..models import EmailMessage, FilterDecision
from .base import EmailFilter
from .rules import FilterRules


def _matches_any(patterns: List[str], text: str) -> List[str]:
    """Return list of patterns that match the text."""
    hits: List[str] = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.I):
            hits.append(pattern)
    return hits


def _count_matches(patterns: List[str], text: str) -> int:
    """Return count of how many patterns match the text."""
    return len(_matches_any(patterns, text))


def _extract_email_address(from_header: str) -> str:
    """Extract email address from From header."""
    match = re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", from_header, re.I)
    return match.group(1).lower() if match else ""


def _domain_of(email_addr: str) -> str:
    """Extract domain from email address."""
    if "@" not in email_addr:
        return ""
    return email_addr.split("@", 1)[1].lower()


def _local_part_of(email_addr: str) -> str:
    """Extract local part (before @) from email address."""
    if "@" not in email_addr:
        return ""
    return email_addr.split("@", 1)[0].lower()


def _is_promotional_sender(email_addr: str, patterns: List[str]) -> bool:
    """Check if the email local part matches promotional sender patterns."""
    local_part = _local_part_of(email_addr)
    if not local_part:
        return False
    # Patterns are designed to match the local part (e.g., ^noreply@)
    # We prepend the local part with nothing and append @ to match properly
    test_str = local_part + "@"
    for pattern in patterns:
        if re.search(pattern, test_str, flags=re.I):
            return True
    return False


def _is_commercial_domain(domain: str, patterns: List[str]) -> bool:
    """Check if domain matches commercial subdomain patterns (e.g., em.*, marketing.*)."""
    if not domain:
        return False
    for pattern in patterns:
        if re.search(pattern, domain, flags=re.I):
            return True
    return False


def _is_known_job_board_domain(domain: str, job_source_domains: List[str]) -> bool:
    """Check if domain is a known job board/ATS (exact match or subdomain)."""
    if not domain:
        return False
    for job_domain in job_source_domains:
        if domain == job_domain or domain.endswith("." + job_domain):
            return True
    return False


class KeywordFilter(EmailFilter):
    """
    Enhanced keyword filter with signal scoring and promotional detection.
    
    The filter uses a scoring system:
    - Strong job signals (recruiter, interview, offer letter, etc.): High confidence
    - Job source domain (greenhouse.io, lever.co, etc.): High confidence
    - Role title patterns (software engineer, etc.): Medium confidence
    - Strong job keywords: Medium confidence
    - Weak job keywords (opportunity, role, position): Low confidence (require multiple)
    
    Negative signals that block or reduce confidence:
    - Non-job domain denylist: Immediate block
    - Commercial domain patterns (em.*, marketing.*): Strong negative
    - Promotional sender patterns (noreply@, marketing@): Strong negative  
    - Promotional/transactional content patterns: Strong negative
    - Marketing footer patterns: Negative signal
    - Education/admissions patterns: Block unless strong job signals
    """
    name = "keyword"

    # Scoring thresholds
    PASS_THRESHOLD = 3  # Minimum score to pass
    STRONG_SIGNAL_SCORE = 4  # Score for strong job signals
    JOB_SOURCE_DOMAIN_SCORE = 5  # Score for known job board domain
    ROLE_TITLE_SCORE = 2  # Score for role title match
    STRONG_KEYWORD_SCORE = 2  # Score per strong keyword (capped)
    WEAK_KEYWORD_SCORE = 0.5  # Score per weak keyword (capped)
    MAX_KEYWORD_SCORE = 4  # Maximum score from keywords
    
    # Negative scoring
    PROMO_SENDER_PENALTY = -3  # Penalty for promotional sender
    COMMERCIAL_DOMAIN_PENALTY = -2  # Penalty for commercial subdomain
    PROMO_CONTENT_PENALTY = -2  # Penalty for promotional content
    TRANSACTIONAL_PENALTY = -3  # Penalty for transactional content
    MARKETING_FOOTER_PENALTY = -1  # Penalty for marketing footer

    def __init__(self, rules: FilterRules | None = None) -> None:
        self.rules = rules or FilterRules.default()

    def _calculate_score(
        self, email: EmailMessage
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate a confidence score for the email being a job opportunity.
        
        Returns:
            Tuple of (score, positive_reasons, negative_reasons)
        """
        from_header = email.headers.from_
        subject = email.headers.subject or ""
        snippet = email.snippet or ""
        body = email.body_text or ""

        text = f"{subject}\n{snippet}\n{body}".strip().lower()
        email_addr = _extract_email_address(from_header)
        domain = _domain_of(email_addr)

        score = 0.0
        positive_reasons: List[str] = []
        negative_reasons: List[str] = []

        # === POSITIVE SIGNALS ===
        
        # 1. Known job source domain (highest confidence)
        if _is_known_job_board_domain(domain, self.rules.job_source_domains):
            score += self.JOB_SOURCE_DOMAIN_SCORE
            positive_reasons.append(f"job source domain: {domain}")

        # 2. Strong job signal patterns
        strong_hits = _matches_any(self.rules.strong_job_signal_patterns, text)
        if strong_hits:
            score += self.STRONG_SIGNAL_SCORE
            positive_reasons.append(f"strong job signals: {len(strong_hits)} matches")

        # 3. Role title patterns
        role_hits = _matches_any(self.rules.role_title_patterns, text)
        if role_hits:
            score += self.ROLE_TITLE_SCORE
            positive_reasons.append("role/title mentioned")

        # 4. Strong job keywords
        strong_kw_hits: List[str] = []
        for keyword in self.rules.job_keywords:
            if keyword in text:
                strong_kw_hits.append(keyword)

        # Context-aware keyword detection
        if "schedule" in text:
            if _matches_any(self.rules.interview_context_patterns, text):
                strong_kw_hits.append("schedule(interview-context)")

        if re.search(r"\boa\b", text, flags=re.I):
            if _matches_any(self.rules.oa_assessment_patterns, text):
                strong_kw_hits.append("oa(assessment-context)")

        if strong_kw_hits:
            kw_score = min(
                len(strong_kw_hits) * self.STRONG_KEYWORD_SCORE,
                self.MAX_KEYWORD_SCORE
            )
            score += kw_score
            uniq = sorted(set(strong_kw_hits))
            positive_reasons.append(
                "strong keywords: "
                + ", ".join(uniq[:5])
                + ("..." if len(uniq) > 5 else "")
            )

        # 5. Weak job keywords (only count if no strong signals)
        weak_kw_hits: List[str] = []
        for keyword in self.rules.weak_job_keywords:
            if keyword in text:
                weak_kw_hits.append(keyword)
        
        if weak_kw_hits and not strong_kw_hits and not strong_hits:
            # Weak keywords only contribute if there are multiple
            if len(weak_kw_hits) >= 3:
                weak_score = min(
                    len(weak_kw_hits) * self.WEAK_KEYWORD_SCORE,
                    self.MAX_KEYWORD_SCORE / 2
                )
                score += weak_score
                uniq = sorted(set(weak_kw_hits))
                positive_reasons.append(
                    "weak keywords (multiple): "
                    + ", ".join(uniq[:5])
                    + ("..." if len(uniq) > 5 else "")
                )

        # === NEGATIVE SIGNALS ===

        # 1. Promotional sender patterns (noreply@, marketing@, etc.)
        if _is_promotional_sender(email_addr, self.rules.promotional_sender_patterns):
            # Only penalize if NOT from a known job source domain
            if not _is_known_job_board_domain(domain, self.rules.job_source_domains):
                score += self.PROMO_SENDER_PENALTY
                local_part = _local_part_of(email_addr)
                negative_reasons.append(f"promotional sender pattern: {local_part}@")

        # 2. Commercial domain patterns (em.*, marketing.*, etc.)
        if _is_commercial_domain(domain, self.rules.commercial_domain_patterns):
            # Only penalize if NOT from a known job source domain
            if not _is_known_job_board_domain(domain, self.rules.job_source_domains):
                score += self.COMMERCIAL_DOMAIN_PENALTY
                negative_reasons.append(f"commercial domain pattern: {domain}")

        # 3. Promotional content patterns
        promo_hits = _matches_any(self.rules.promo_negative_patterns, text)
        if promo_hits:
            score += self.PROMO_CONTENT_PENALTY
            negative_reasons.append(f"promotional content: {len(promo_hits)} patterns")

        # 4. Transactional patterns
        transactional_hits = _matches_any(self.rules.transactional_patterns, text)
        if transactional_hits:
            score += self.TRANSACTIONAL_PENALTY
            negative_reasons.append(f"transactional content: {len(transactional_hits)} patterns")

        # 5. Marketing footer patterns
        footer_hits = _matches_any(self.rules.marketing_footer_patterns, text)
        if footer_hits:
            score += self.MARKETING_FOOTER_PENALTY
            negative_reasons.append("marketing footer detected")

        return score, positive_reasons, negative_reasons

    def evaluate(self, email: EmailMessage) -> FilterDecision:
        from_header = email.headers.from_
        subject = email.headers.subject or ""
        snippet = email.snippet or ""
        body = email.body_text or ""

        text = f"{subject}\n{snippet}\n{body}".strip().lower()
        email_addr = _extract_email_address(from_header)
        domain = _domain_of(email_addr)

        # === IMMEDIATE BLOCKS (domain denylist) ===
        if domain and domain in self.rules.non_job_domains:
            return FilterDecision(
                filter_name=self.name,
                passed=False,
                reasons=[f"non-job domain denylist: {domain}"],
            )

        # === EDUCATION/ADMISSIONS BLOCK ===
        edu_hits = _matches_any(self.rules.edu_negative_patterns, text)
        strong_hits = _matches_any(self.rules.strong_job_signal_patterns, text)
        
        if edu_hits and not strong_hits:
            # Block education emails unless they have strong job signals
            return FilterDecision(
                filter_name=self.name,
                passed=False,
                reasons=["education/admissions pattern (no strong job signals)"],
            )

        # === CALCULATE SCORE ===
        score, positive_reasons, negative_reasons = self._calculate_score(email)

        # Combine reasons for reporting
        all_reasons = positive_reasons + negative_reasons
        all_reasons.append(f"score: {score:.1f} (threshold: {self.PASS_THRESHOLD})")

        # === DECISION ===
        if score >= self.PASS_THRESHOLD:
            return FilterDecision(
                filter_name=self.name,
                passed=True,
                reasons=all_reasons,
            )
        else:
            if not positive_reasons:
                return FilterDecision(
                    filter_name=self.name,
                    passed=False,
                    reasons=["no positive job signals"] + negative_reasons,
                )
            else:
                return FilterDecision(
                    filter_name=self.name,
                    passed=False,
                    reasons=["insufficient job signals"] + all_reasons,
                )
