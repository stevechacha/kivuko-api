"""Stateful WhatsApp civic learning bot — menu, quiz, lessons, timeline."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

from api.models import AcademyArticle, QuizQuestion, TimelineEvent, WhatsAppSession

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
POINTS_PER_CORRECT = 10
WEB_BASE = getattr(settings, "PUBLIC_APP_BASE_URL", "https://kivuko-web-production.up.railway.app").rstrip("/")


@dataclass
class BotReply:
    text: str
    suggestions: list[str] = field(default_factory=list)
    points: int = 0


def _default_state() -> dict[str, Any]:
    return {
        "mode": "idle",
        "quiz_index": 0,
        "quiz_correct": 0,
        "lesson_category": None,
        "history_index": 0,
    }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _option_letter(index: int) -> str:
    return LETTERS[index] if index < len(LETTERS) else str(index + 1)


def _format_options(options: list[str]) -> str:
    lines = []
    for i, opt in enumerate(options):
        lines.append(f"{_option_letter(i)}) {opt}")
    return "\n".join(lines)


def _menu_text(points: int) -> str:
    total = len(_quiz_questions())
    quiz_line = f"1️⃣ *JARIBIO* — Maswali {total} ya historia ya Muungano"
    pts = f"\n⭐ Pointi zako: *{points}*" if points else ""
    return (
        "📋 *Menyu ya Kivuko Bot*\n\n"
        "Chagua kwa kuandika neno au namba:\n\n"
        f"{quiz_line}\n"
        "2️⃣ *SOMO* — Somo fupi kutoka Makumbusho\n"
        "3️⃣ *HISTORIA* — Mstari wa safari ya taifa\n"
        "4️⃣ *USAJILI* — Jiunge na dhamira za pamoja\n"
        "5️⃣ *POINTI* — Angalia pointi zako"
        f"{pts}\n\n"
        "Andika *MSAADA* kwa mwongozo kamili."
    )


def _welcome_text() -> str:
    return (
        "Habari Mzalendo! 🌊🇹🇿\n\n"
        "Mimi ni *Kivuko Bot* — msaidizi wako wa elimu ya uzalendo "
        "kupitia WhatsApp.\n\n"
        "Ninaweza kukufundisha historia ya Muungano, kukupa maswali ya jaribio, "
        "na kukuongoza kujisajili kwenye wavuti kwa cheti cha QR.\n\n"
        + _menu_text(0)
    )


def _help_text() -> str:
    return (
        "ℹ️ *Mwongozo wa Kivuko Bot*\n\n"
        "• *MENYU* — onyesha menyu kuu\n"
        "• *JARIBIO* — anza maswali (jibu A, B, C au 1, 2, 3)\n"
        "• *ENDELEA* — swali linalofuata (ukiko kwenye jaribio)\n"
        "• *SOMO* — somo fupi la uzalendo / muungano / jeshi\n"
        "• *HISTORIA* — matukio muhimu 1961 — leo\n"
        "• *USAJILI* — kiungo cha kujisajili bure\n"
        "• *POINTI* — jumla ya pointi za kipindi hiki\n"
        "• *STOP* — maliza na uanze upya\n\n"
        "Kwa dhamira kamili na cheti: tembelea wavuti yetu."
    )


def _register_text() -> str:
    return (
        "📱 *Jisajili kwenye Kivuko la Muungano Hub*\n\n"
        "1. Fungua: " + WEB_BASE + "/usajili\n"
        "2. Jaza jina, simu, chuo, na mkoa wako\n"
        "3. Kamilisha *Dhamira 5* na pacha kutoka Bara au Visiwani\n"
        "4. Pata *Cheti cha QR* kinachothibitishwa\n\n"
        "Bure kabisa kwa vijana wa Tanzania! 🇹🇿"
    )


def _lesson_menu_text() -> str:
    return (
        "📚 *Chagua Somo*\n\n"
        "1 — Historia ya Muungano (1964)\n"
        "2 — Historia ya JWTZ / Jeshi\n"
        "3 — Misingi ya Uzalendo\n\n"
        "Andika namba 1, 2, au 3."
    )


def _lesson_for_choice(choice: str) -> tuple[str, str] | None:
    mapping = {
        "1": "union",
        "2": "army",
        "3": "patriot",
        "muungano": "union",
        "union": "union",
        "jeshi": "army",
        "army": "army",
        "jwtz": "army",
        "uzalendo": "patriot",
        "patriot": "patriot",
    }
    cat = mapping.get(choice)
    if not cat:
        return None
    article = AcademyArticle.objects.filter(category=cat).order_by("sort_order").first()
    if not article:
        return None
    body_preview = article.body.replace("\n\n", "\n").strip()
    if len(body_preview) > 420:
        body_preview = body_preview[:417].rstrip() + "…"
    text = (
        f"📖 *{article.title}*\n\n"
        f"{article.summary}\n\n"
        f"{body_preview}\n\n"
        "Tembelea *Makumbusho* kwenye wavuti kwa somo kamili."
    )
    return text, cat


def _quiz_questions() -> list[QuizQuestion]:
    return list(QuizQuestion.objects.order_by("sort_order"))


def _format_quiz_question(q: QuizQuestion, index: int, total: int) -> str:
    return (
        f"📝 *Swali {index + 1}/{total}*\n\n"
        f"{q.question}\n\n"
        f"{_format_options(q.options)}\n\n"
        "Jibu kwa herufi (A, B, C) au namba."
    )


def _parse_answer(text: str, options: list[str]) -> int | None:
    lowered = _normalize(text)
    if not lowered:
        return None

    # Letter answer: a, b, c
    letter_match = re.match(r"^([a-z])\.?$", lowered)
    if letter_match:
        idx = ord(letter_match.group(1)) - ord("a")
        if 0 <= idx < len(options):
            return idx

    # Numeric answer: 1, 2, 3
    num_match = re.match(r"^(\d+)\.?$", lowered)
    if num_match:
        idx = int(num_match.group(1)) - 1
        if 0 <= idx < len(options):
            return idx

    # Partial text match on option
    for i, opt in enumerate(options):
        opt_lower = opt.lower()
        if lowered in opt_lower or opt_lower in lowered:
            return i
        # Match first significant word
        words = [w for w in re.split(r"\W+", opt_lower) if len(w) > 3]
        if any(w in lowered for w in words):
            return i

    return None


def _history_page(index: int) -> tuple[str, int, int]:
    events = list(TimelineEvent.objects.order_by("sort_order"))
    total = len(events)
    if not events:
        return "Hakuna matukio ya historia kwa sasa.", 0, 0
    idx = index % total
    ev = events[idx]
    month = f" {ev.month_label}" if ev.month_label else ""
    text = (
        f"📅 *{ev.year}{month}*\n"
        f"*{ev.title}*\n\n"
        f"{ev.description}\n\n"
        f"({idx + 1}/{total}) — Andika *ENDELEA* kwa tukio linalofuata."
    )
    return text, idx, total


def _get_or_create_session(session_id: str | None) -> WhatsAppSession:
    if session_id:
        existing = WhatsAppSession.objects.filter(session_key=session_id).first()
        if existing:
            return existing
    key = session_id or secrets.token_urlsafe(18)
    return WhatsAppSession.objects.create(
        session_key=key,
        points=0,
        state=_default_state(),
    )


def _save_session(session: WhatsAppSession) -> None:
    session.save(update_fields=["points", "state", "updated_at"])


def handle_whatsapp_message(text: str, session_id: str | None = None) -> tuple[BotReply, str]:
    session = _get_or_create_session(session_id)
    state = {**_default_state(), **(session.state or {})}
    raw = text.strip()
    lowered = _normalize(raw)

    def reply(msg: str, suggestions: list[str] | None = None) -> tuple[BotReply, str]:
        session.state = state
        _save_session(session)
        default_suggestions = suggestions or ["MENYU", "JARIBIO", "USAJILI"]
        return BotReply(text=msg, suggestions=default_suggestions, points=session.points), session.session_key

    # Global commands (work in any mode)
    if lowered in ("stop", "ondoka", "quit", "exit"):
        state = _default_state()
        return reply(
            "Asante kwa kujifunza nasi! 🇹🇿\nAndika *MUUNGANO* au *MENYU* uanze tena.",
            ["MUUNGANO", "JARIBIO"],
        )

    if lowered in ("msaada", "help", "?", "saidia"):
        return reply(_help_text(), ["JARIBIO", "SOMO", "USAJILI"])

    if lowered in ("menyu", "menu", "0"):
        state["mode"] = "idle"
        return reply(_menu_text(session.points), ["JARIBIO", "SOMO", "HISTORIA"])

    if lowered in ("pointi", "points", "5"):
        return reply(
            f"⭐ *Pointi zako za Uzalendo:* {session.points}\n\n"
            "Kila jibu sahihi la jaribio = +10 pointi.\n"
            "Kamilisha dhamira kwenye wavuti kwa pointi zaidi na cheti cha QR!",
            ["JARIBIO", "USAJILI", "MENYU"],
        )

    if lowered in ("usajili", "simu", "web", "wavuti", "register", "4", "jiunge"):
        return reply(_register_text(), ["USAJILI", "JARIBIO", "MENYU"])

    # Mode-specific handling
    mode = state.get("mode", "idle")

    if mode == "quiz":
        return _handle_quiz_mode(raw, lowered, state, session, reply)

    if mode == "lesson":
        return _handle_lesson_mode(lowered, state, session, reply)

    if mode == "history":
        return _handle_history_mode(lowered, state, session, reply)

    # Idle mode — entry commands
    if not lowered:
        return reply(_welcome_text(), ["JARIBIO", "SOMO", "USAJILI"])

    if lowered in ("muungano", "start", "anza", "hi", "habari", "hello", "salama"):
        return reply(_welcome_text(), ["JARIBIO", "SOMO", "USAJILI"])

    if lowered in ("jaribio", "quiz", "maswali", "1"):
        questions = _quiz_questions()
        if not questions:
            return reply("Maswali hayajapatikana kwa sasa. Jaribu tena baadaye.", ["MENYU"])
        state["mode"] = "quiz"
        # Resume mid-quiz unless user asks to restart
        if lowered not in ("anza", "start", "upya", "reset") and state.get("quiz_index", 0) > 0:
            idx = min(int(state.get("quiz_index", 0)), len(questions) - 1)
        else:
            state["quiz_index"] = 0
            state["quiz_correct"] = 0
            idx = 0
        total = len(questions)
        return reply(
            _format_quiz_question(questions[idx], idx, total),
            ["A", "B", "C"],
        )

    if lowered in ("somo", "elimu", "makumbusho", "2"):
        state["mode"] = "lesson"
        return reply(_lesson_menu_text(), ["1", "2", "3"])

    if lowered in ("historia", "timeline", "mstari", "3"):
        state["mode"] = "history"
        state["history_index"] = 0
        msg, _, _ = _history_page(0)
        return reply(msg, ["ENDELEA", "MENYU"])

    if "?" in raw and len(lowered) > 8:
        return reply(
            "Swali zuri! 🙏\nKwa majibu ya kina, jaribu *JARIBIO*, *SOMO*, au jiunge kwenye wavuti.",
            ["JARIBIO", "SOMO", "USAJILI"],
        )

    return reply(
        "Samahani, sijaelewa. Andika *MENYU* kuona chaguo, au *MSAADA* kwa mwongozo.",
        ["MENYU", "JARIBIO", "MSAADA"],
    )


def _handle_quiz_mode(
    raw: str,
    lowered: str,
    state: dict[str, Any],
    session: WhatsAppSession,
    reply,
) -> tuple[BotReply, str]:
    questions = _quiz_questions()
    total = len(questions)
    if not total:
        state["mode"] = "idle"
        return reply("Hakuna maswali kwa sasa.", ["MENYU"])

    idx = int(state.get("quiz_index", 0))
    if idx >= total:
        idx = 0
        state["quiz_index"] = 0

    if lowered in ("endelea", "next", "ijayo", "swali"):
        idx = (idx + 1) % total
        state["quiz_index"] = idx
        return reply(_format_quiz_question(questions[idx], idx, total), ["A", "B", "C"])

    if lowered in ("menyu", "menu", "acha", "stop"):
        state["mode"] = "idle"
        correct = state.get("quiz_correct", 0)
        return reply(
            f"Umemaliza jaribio kwa sasa. ✅ Sahihi: {correct}/{total}\n⭐ Pointi: {session.points}\n\n"
            + _menu_text(session.points),
            ["JARIBIO", "MENYU"],
        )

    q = questions[idx]
    chosen = _parse_answer(raw, q.options)
    if chosen is None:
        return reply(
            "Tafadhali jibu kwa herufi *A*, *B*, *C* au namba *1*, *2*, *3*.\nAu andika *ENDELEA* kwa swali linalofuata.",
            ["A", "B", "C"],
        )

    if chosen == q.correct_index:
        session.points += POINTS_PER_CORRECT
        state["quiz_correct"] = int(state.get("quiz_correct", 0)) + 1
        next_idx = (idx + 1) % total
        state["quiz_index"] = next_idx
        if next_idx == 0 and idx == total - 1:
            state["mode"] = "idle"
            correct = state["quiz_correct"]
            return reply(
                f"🎉 *Hongera!* Umekamilisha maswali yote!\n\n"
                f"✅ Sahihi: {correct}/{total}\n"
                f"⭐ Jumla pointi: {session.points}\n\n"
                "Jiunge kwenye wavuti kwa dhamira za pamoja na cheti cha QR.\n\n"
                + _register_text(),
                ["USAJILI", "JARIBIO", "MENYU"],
            )
        return reply(
            f"✅ *Sahihi!* +{POINTS_PER_CORRECT} Pointi za Uzalendo\n"
            f"⭐ Jumla: {session.points}\n\n"
            + _format_quiz_question(questions[next_idx], next_idx, total),
            ["A", "B", "C"],
        )

    correct_label = _option_letter(q.correct_index)
    correct_answer = q.options[q.correct_index]
    next_idx = (idx + 1) % total
    state["quiz_index"] = next_idx
    return reply(
        f"❌ Si sahihi. Jibu sahihi: *{correct_label}) {correct_answer}*\n\n"
        + _format_quiz_question(questions[next_idx], next_idx, total),
        ["A", "B", "C"],
    )


def _handle_lesson_mode(
    lowered: str,
    state: dict[str, Any],
    session: WhatsAppSession,
    reply,
) -> tuple[BotReply, str]:
    if lowered in ("menyu", "menu", "back", "rudi"):
        state["mode"] = "idle"
        return reply(_menu_text(session.points), ["JARIBIO", "SOMO"])

    result = _lesson_for_choice(lowered)
    if result:
        text, _cat = result
        return reply(text, ["SOMO", "JARIBIO", "MENYU"])

    return reply(
        _lesson_menu_text() + "\n\nAu andika *MENYU* kurudi.",
        ["1", "2", "3"],
    )


def _handle_history_mode(
    lowered: str,
    state: dict[str, Any],
    session: WhatsAppSession,
    reply,
) -> tuple[BotReply, str]:
    if lowered in ("menyu", "menu", "back", "rudi"):
        state["mode"] = "idle"
        return reply(_menu_text(session.points), ["HISTORIA", "MENYU"])

    idx = int(state.get("history_index", 0))
    if lowered in ("endelea", "next", "ijayo", "mbele"):
        events = list(TimelineEvent.objects.order_by("sort_order"))
        total = len(events) or 1
        idx = (idx + 1) % total
        state["history_index"] = idx

    msg, _, _ = _history_page(idx)
    return reply(msg, ["ENDELEA", "MENYU"])
