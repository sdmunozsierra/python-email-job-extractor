from __future__ import annotations

import base64
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def get_header(headers: List[Dict[str, str]], name: str) -> str:
    name_l = name.lower()
    for header in headers:
        if header.get("name", "").lower() == name_l:
            return header.get("value", "")
    return ""


def extract_email_address(from_header: str) -> str:
    match = re.search(r"([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})", from_header, re.I)
    return match.group(1).lower() if match else ""


def domain_of(email_addr: str) -> str:
    if "@" not in email_addr:
        return ""
    return email_addr.split("@", 1)[1].lower()


def _b64url_decode(data: str) -> bytes:
    pad = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + pad)


def strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style).*?>.*?</\1>", "", html)
    html = re.sub(r"(?i)<br\s*/?>", "\n", html)
    html = re.sub(r"(?i)</p\s*>", "\n\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def walk_mime_for_text(payload: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    text_plain = None
    text_html = None

    def walk(part: Dict[str, Any]) -> None:
        nonlocal text_plain, text_html
        mime = (part.get("mimeType") or "").lower()
        body = part.get("body", {}) or {}
        data = body.get("data")

        if data:
            try:
                decoded = _b64url_decode(data).decode("utf-8", errors="replace")
            except Exception:
                decoded = _b64url_decode(data).decode(errors="replace")

            if mime == "text/plain" and text_plain is None:
                text_plain = decoded
            elif mime == "text/html" and text_html is None:
                text_html = decoded

        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return text_plain, text_html


def extract_body_text(full_msg: Dict[str, Any]) -> Dict[str, str]:
    payload = full_msg.get("payload", {}) or {}
    text_plain, text_html = walk_mime_for_text(payload)

    chosen = ""
    chosen_type = "none"
    if text_plain and text_plain.strip():
        chosen = text_plain
        chosen_type = "text/plain"
    elif text_html and text_html.strip():
        chosen = strip_html(text_html)
        chosen_type = "text/html->text"

    return {
        "chosen_type": chosen_type,
        "text": normalize_text(chosen),
        "text_plain": normalize_text(text_plain or ""),
        "text_html": text_html or "",
    }


def list_attachments(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def walk(part: Dict[str, Any]) -> None:
        filename = part.get("filename") or ""
        body = part.get("body", {}) or {}
        attachment_id = body.get("attachmentId")
        mime = part.get("mimeType") or ""
        size = body.get("size", 0)

        if attachment_id and filename:
            out.append(
                {
                    "filename": filename,
                    "mimeType": mime,
                    "size": size,
                    "attachmentId": attachment_id,
                }
            )

        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    return out


def parse_internal_date_ms(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromtimestamp(int(value) / 1000, tz=timezone.utc)
