"""USSD channel adapter — reuses the live WhatsApp bot engine with plain-text output."""

from __future__ import annotations

import re

from api.whatsapp_bot import handle_whatsapp_message


def _strip_markdown(text: str) -> str:
    cleaned = re.sub(r"\*+", "", text)
    cleaned = re.sub(r"[0-9]️⃣", "", cleaned)
    return cleaned.strip()


def handle_ussd_message(text: str, session_id: str | None = None) -> dict:
    reply, sid = handle_whatsapp_message(text, session_id)
    lines = [_strip_markdown(line) for line in reply.text.split("\n") if line.strip()]
    suggestions = [_strip_markdown(s) for s in reply.suggestions if s.strip()]
    return {
        "session_id": sid,
        "lines": lines[:10],
        "suggestions": suggestions[:6],
        "points": reply.points,
    }
