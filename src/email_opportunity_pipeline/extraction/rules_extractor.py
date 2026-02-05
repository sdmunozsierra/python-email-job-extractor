from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from ..models import EmailMessage
from .extractor import BaseExtractor


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def _parse_from_header(from_header: str) -> Tuple[Optional[str], Optional[str]]:
    match = re.match(r"(?P<name>.+?)\s*<(?P<email>[^>]+)>", from_header)
    if match:
        return match.group("name").strip('" '), match.group("email").strip()
    if "@" in from_header:
        return None, from_header.strip()
    return from_header.strip() or None, None


def _extract_phone(text: str) -> Optional[str]:
    match = re.search(r"(\+?\d{1,2}[\s.-]?)?(\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4})", text)
    return match.group(0).strip() if match else None


def _extract_links(text: str) -> List[str]:
    return re.findall(r"https?://[^\s)>\"]+", text)


def _extract_company_from_email(email: Optional[str]) -> Optional[str]:
    if not email or "@" not in email:
        return None
    domain = email.split("@", 1)[1]
    return domain.split(".")[0].replace("-", " ").title()


def _extract_locations(text: str) -> List[str]:
    locations: List[str] = []
    for match in re.finditer(r"(?:location|locations)\s*[:\-]\s*(.+)", text, flags=re.I):
        candidate = match.group(1).strip()
        if candidate:
            locations.append(candidate)
    return _dedupe(locations)


def _extract_section_list(text: str, label_patterns: List[str]) -> List[str]:
    for label in label_patterns:
        match = re.search(label, text, flags=re.I)
        if match:
            block = match.group(1).strip()
            items = re.split(r"[,\n;|]+", block)
            return _dedupe([item.strip() for item in items if item.strip()])
    return []


def _extract_pay(text: str) -> Dict[str, Optional[float | str]]:
    currency = "USD" if "$" in text or "usd" in text.lower() else None
    unit = None
    unit_match = re.search(r"\b(per|/)\s*(hour|hr|year|yr|day)\b", text, flags=re.I)
    if unit_match:
        unit = unit_match.group(2).lower()
        if unit in {"hr", "hour"}:
            unit = "hour"
        if unit in {"yr", "year"}:
            unit = "year"

    range_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*[-–]\s*\$?\s*(\d+(?:\.\d+)?)\s*(k|K)?", text)
    if range_match:
        min_val = float(range_match.group(1))
        max_val = float(range_match.group(2))
        if range_match.group(3):
            min_val *= 1000
            max_val *= 1000
        return {"min": min_val, "max": max_val, "currency": currency, "unit": unit, "notes": None}

    single_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(k|K)?", text)
    if single_match:
        value = float(single_match.group(1))
        if single_match.group(2):
            value *= 1000
        return {"min": value, "max": value, "currency": currency, "unit": unit, "notes": None}

    return {"min": None, "max": None, "currency": currency, "unit": unit, "notes": None}


def _infer_engagement_options(text: str) -> List[Dict[str, object]]:
    lower = text.lower()
    types: List[str] = []

    if "full time" in lower or "full-time" in lower:
        types.append("FULL_TIME")
    if "part time" in lower or "part-time" in lower:
        types.append("PART_TIME")
    if re.search(r"\bc2c\b|corp[- ]to[- ]corp", lower):
        types.append("CONTRACT_C2C")
    if re.search(r"\bw2\b", lower):
        types.append("CONTRACT_W2")
    if "1099" in lower:
        types.append("CONTRACT_1099")
    if "contract" in lower and not types:
        types.append("CONTRACT_W2")

    if not types:
        types.append("UNKNOWN")

    return [
        {
            "type": t,
            "duration": None,
            "pay": {"min": None, "max": None, "currency": None, "unit": None, "notes": None},
            "benefits_notes": None,
            "constraints": [],
            "differences_vs_other_options": [],
            "evidence": [],
        }
        for t in _dedupe(types)
    ]


def _extract_title(subject: str, body: str) -> Optional[str]:
    subject = re.sub(r"^(re:|fwd:)\s*", "", subject.strip(), flags=re.I)
    if subject:
        if "location" in subject.lower():
            title = subject.split("Location", 1)[0].strip(" -:")
            if title:
                return title
        return subject
    for line in body.splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return None


class RuleBasedExtractor(BaseExtractor):
    def extract(self, email: EmailMessage) -> Dict:
        subject = email.headers.subject or ""
        body = email.body_text or ""
        text = f"{subject}\n{body}"

        recruiter_name, recruiter_email = _parse_from_header(email.headers.from_)
        recruiter_company = None
        if recruiter_name and "(" in recruiter_name and ")" in recruiter_name:
            recruiter_company = recruiter_name.split("(", 1)[1].split(")", 1)[0]
            recruiter_name = recruiter_name.split("(", 1)[0].strip()

        if not recruiter_company:
            recruiter_company = _extract_company_from_email(recruiter_email)

        title = _extract_title(subject, body)
        locations = _extract_locations(text)
        remote = True if "remote" in text.lower() else None
        hybrid = True if "hybrid" in text.lower() else None

        mandatory = _extract_section_list(
            text,
            [
                r"mandatory skills\s*[:\-]\s*(.+)",
                r"primary skill set\s*[:\-]\s*(.+)",
            ],
        )
        preferred = _extract_section_list(text, [r"preferred skills\s*[:\-]\s*(.+)"])
        responsibilities = _extract_section_list(text, [r"responsibilities\s*[:\-]\s*(.+)"])
        qualifications = _extract_section_list(text, [r"qualifications\s*[:\-]\s*(.+)"])

        constraints: List[str] = []
        if re.search(r"us citizens? only|must be us citizens?", text, flags=re.I):
            constraints.append("US citizens only")
        if re.search(r"no sponsorship|without sponsorship", text, flags=re.I):
            constraints.append("No sponsorship")

        engagement_options = _infer_engagement_options(text)
        pay = _extract_pay(text)
        for option in engagement_options:
            option["pay"] = pay
            option["constraints"] = constraints
            option["evidence"] = []

        links = _extract_links(body)
        apply_link = links[0] if links else None

        evidence: List[str] = []
        if subject:
            evidence.append(subject)
        if locations:
            evidence.append(f"Location: {', '.join(locations)}")
        if constraints:
            evidence.append("; ".join(constraints))
        if pay.get("min") or pay.get("max"):
            evidence.append("Pay mentioned in email")

        job = {
            "job_title": title,
            "company": recruiter_company,
            "recruiter_name": recruiter_name,
            "recruiter_company": recruiter_company,
            "recruiter_email": recruiter_email,
            "recruiter_phone": _extract_phone(body),
            "social_links": _dedupe([link for link in links if "linkedin.com" in link]),
            "locations": locations,
            "remote": remote,
            "hybrid": hybrid,
            "summary": email.snippet or None,
            "hard_requirements": constraints,
            "mandatory_skills": mandatory,
            "preferred_skills": preferred,
            "responsibilities": responsibilities,
            "qualifications": qualifications,
            "engagement_options": engagement_options,
            "apply_link": apply_link,
            "source_email": {
                "message_id": email.message_id,
                "thread_id": email.thread_id,
                "subject": subject or None,
                "from": email.headers.from_ or None,
                "date": email.headers.date or None,
            },
            "evidence": evidence,
            "missing_fields": [],
            "confidence": 0.3,
        }

        missing = []
        for key in [
            "job_title",
            "company",
            "recruiter_email",
            "locations",
            "mandatory_skills",
        ]:
            value = job.get(key)
            if value is None or (isinstance(value, list) and not value):
                missing.append(key)
        job["missing_fields"] = missing

        base = 0.2
        base += 0.1 if title else 0
        base += 0.1 if locations else 0
        base += 0.1 if recruiter_email else 0
        base += 0.1 if mandatory else 0
        job["confidence"] = min(1.0, base)

        return job
