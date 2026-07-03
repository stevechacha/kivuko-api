"""Automated chat safety — keyword and pattern detection (proposal TC-06)."""

from __future__ import annotations

import re

ABUSIVE_TERMS = (
    "fala",
    "mjinga",
    "stupid",
    "idiot",
    "kuma",
    "mbwa",
    "hate",
    "chuki",
    "ua ",
    "kill",
)

CONTACT_PATTERNS = (
    re.compile(r"\b0[67]\d{8}\b"),
    re.compile(r"\b\+?255[67]\d{8}\b"),
    re.compile(r"\bwhatsapp\b", re.I),
    re.compile(r"\bwhat'?s\s*app\b", re.I),
    re.compile(r"\binstagram\b", re.I),
    re.compile(r"\btelegram\b", re.I),
    re.compile(r"\bnamba\s+yangu\b", re.I),
    re.compile(r"\bmy\s+number\b", re.I),
    re.compile(r"\bcall\s+me\b", re.I),
)

INAPPROPRIATE_TERMS = (
    "ngono",
    "sex",
    "porn",
    "uchawi",
)


def detect_violation(text: str) -> tuple[bool, str | None]:
    """Return (should_flag, reason_code)."""
    lowered = text.lower().strip()
    if not lowered:
        return False, None

    for pat in CONTACT_PATTERNS:
        if pat.search(lowered):
            return True, "contact_request"

    for term in ABUSIVE_TERMS:
        if term in lowered:
            return True, "abusive_language"

    for term in INAPPROPRIATE_TERMS:
        if term in lowered:
            return True, "inappropriate_content"

    return False, None
