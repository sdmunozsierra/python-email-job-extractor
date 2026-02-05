"""Utility: convert free-text strings into lists."""

from __future__ import annotations

import re
from typing import List


def convert_to_list(text: str) -> List[str]:
    """Split a free-text string into a list of items.

    Handles comma-separated, semicolon-separated, bullet-pointed, and
    newline-separated text.
    """
    if not text:
        return []

    # Try bullet points first
    bullets = re.findall(r"[•\-\*]\s*(.+)", text)
    if bullets:
        return [b.strip() for b in bullets if b.strip()]

    # Try numbered list
    numbered = re.findall(r"\d+[\.\)]\s*(.+)", text)
    if numbered:
        return [n.strip() for n in numbered if n.strip()]

    # Comma / semicolon separated
    if ";" in text:
        return [s.strip() for s in text.split(";") if s.strip()]
    if "," in text:
        return [s.strip() for s in text.split(",") if s.strip()]

    # Newline separated
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) > 1:
        return lines

    return [text.strip()] if text.strip() else []
