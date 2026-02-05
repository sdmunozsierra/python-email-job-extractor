from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class FilterRules:
    job_source_domains: List[str] = field(default_factory=list)
    non_job_domains: List[str] = field(default_factory=list)
    job_keywords: List[str] = field(default_factory=list)
    role_title_patterns: List[str] = field(default_factory=list)
    promo_negative_patterns: List[str] = field(default_factory=list)
    edu_negative_patterns: List[str] = field(default_factory=list)
    strong_job_signal_patterns: List[str] = field(default_factory=list)
    interview_context_patterns: List[str] = field(default_factory=list)
    oa_assessment_patterns: List[str] = field(default_factory=list)

    @classmethod
    def default(cls) -> "FilterRules":
        return cls(
            job_source_domains=[
                "greenhouse.io",
                "lever.co",
                "workable.com",
                "icims.com",
                "ashbyhq.com",
                "smartrecruiters.com",
                "myworkday.com",
                "jobvite.com",
                "linkedin.com",
                "indeed.com",
                "glassdoor.com",
            ],
            non_job_domains=[
                "e.allegiant.com",
                "email.meetup.com",
                "announcements.soundcloud.com",
                "emaildl.att-mail.com",
                "sfmc2.edx.org",
            ],
            job_keywords=[
                "recruiter",
                "recruiting",
                "talent acquisition",
                "talent partner",
                "sourcer",
                "opportunity",
                "role",
                "position",
                "opening",
                "vacancy",
                "are you open to",
                "are you interested",
                "would you be interested",
                "quick chat",
                "calendar link",
                "job description",
                "jd",
                "responsibilities",
                "requirements",
                "offer",
                "offer letter",
                "compensation",
                "base salary",
                "equity",
                "rsu",
                "bonus",
                "benefits",
                "relocation",
                "visa sponsorship",
                "sponsorship",
                "start date",
                "background check",
                "application",
                "applied",
                "candidate",
                "candidacy",
                "submission",
                "resume",
                "cv",
                "portfolio",
                "cover letter",
                "screening",
                "phone screen",
                "interview",
                "interview loop",
                "take-home",
                "assignment",
                "assessment",
                "coding challenge",
                "technical screen",
                "onsite",
                "final round",
                "next steps",
                "time slots",
                "internship",
                "co-op",
                "apprenticeship",
                "graduate program",
                "new grad",
                "job alert",
                "jobs you may like",
                "new jobs",
                "recommended jobs",
                "saved job",
                "application status",
                "your application",
                "no longer under consideration",
                "we decided to move forward",
                "thank you for applying",
            ],
            role_title_patterns=[
                r"\bsoftware engineer\b",
                r"\bdeveloper\b",
                r"\bdata scientist\b",
                r"\bnlp\b",
                r"\bml engineer\b|\bmachine learning\b",
                r"\bproduct manager\b",
                r"\bproject manager\b",
                r"\bdevops\b",
                r"\bsite reliability\b|\bsre\b",
                r"\bsecurity engineer\b",
                r"\bsolutions engineer\b",
                r"\bsales engineer\b",
                r"\baccount executive\b",
                r"\bsdr\b|\bbdr\b",
                r"\bsales ops\b",
                r"\bsalesforce\b",
                r"\bcustomer success\b",
                r"\bprincipal\b|\bstaff\b|\bsenior\b|\bjunior\b",
                r"\banalyst\b",
                r"\binternship\b",
                r"\bintern\b(?!et)\b",
            ],
            promo_negative_patterns=[
                r"\bfree shipping\b",
                r"\bpromo code\b",
                r"\bcoupon\b",
                r"\bdiscount\b",
                r"\bclearance\b",
                r"\bflash sale\b",
                r"\border (confirmed|confirmation)\b",
                r"\bshipping (update|notification)\b",
                r"\bdelivered\b",
                r"\btracking number\b",
                r"\byour cart\b",
                r"\bnewsletter\b",
                r"\bunsubscribe\b",
                r"\byour (online )?bill\b",
                r"\bbill is ready\b",
                r"\bpayment due\b",
                r"\baccount number\b",
            ],
            edu_negative_patterns=[
                r"\badmissions?\b",
                r"\bapply(ing|)\b.*\b(program|degree|master|ms|m\.s\.|mba|certificate)\b",
                r"\bonline master\b",
                r"\buniversity\b",
                r"\bschool of\b",
                r"\bberkeley\b",
                r"\bedx\b",
                r"\btuition\b",
                r"\benroll\b",
                r"\bgraduate program\b",
            ],
            strong_job_signal_patterns=[
                r"\boffer letter\b",
                r"\binterview\b",
                r"\bphone screen\b",
                r"\btechnical screen\b",
                r"\bonsite\b",
                r"\bfinal round\b",
                r"\brecruit(er|ing)\b|\btalent acquisition\b|\bsourcer\b",
                r"\bapplication (received|submitted|status)\b",
                r"\bcandidate\b",
                r"\bbackground check\b",
                r"\bjob description\b|\bresponsibilities\b|\brequirements\b",
                r"\bcompensation\b|\bbase salary\b|\bequity\b|\brsu\b",
                r"\binternship\b|\bintern\b(?!et)\b|\bco-?op\b|\bapprenticeship\b",
            ],
            interview_context_patterns=[
                r"\binterview\b",
                r"\bphone screen\b",
                r"\btechnical screen\b",
                r"\bonsite\b",
                r"\bfinal round\b",
                r"\brecruit(er|ing)\b",
                r"\btalent acquisition\b",
            ],
            oa_assessment_patterns=[
                r"\b(online assessment|assessment|coding challenge|take[- ]home|hacker(rank)?|codesignal|codility|karat)\b",
            ],
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterRules":
        base = cls.default()
        for key, value in data.items():
            if hasattr(base, key):
                setattr(base, key, value)
        return base

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_source_domains": self.job_source_domains,
            "non_job_domains": self.non_job_domains,
            "job_keywords": self.job_keywords,
            "role_title_patterns": self.role_title_patterns,
            "promo_negative_patterns": self.promo_negative_patterns,
            "edu_negative_patterns": self.edu_negative_patterns,
            "strong_job_signal_patterns": self.strong_job_signal_patterns,
            "interview_context_patterns": self.interview_context_patterns,
            "oa_assessment_patterns": self.oa_assessment_patterns,
        }


def load_rules(path: str | Path) -> FilterRules:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return FilterRules.from_dict(data)
