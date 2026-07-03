"""Rule-based Kiswahili Union history tutor (Tier 3 light — no external AI dependency)."""

from __future__ import annotations

TUTOR_KB = [
    (
        ("muungano", "union", "1964", "26 april", "april 26"),
        "Muungano wa Tanganyika na Zanzibar ulianzishwa 26 Aprili 1964, na kuunda Jamhuri ya Muungano wa Tanzania.",
    ),
    (
        ("nyerere", "mwalimu"),
        "Mwalimu Julius Nyerere aliongoza Tanganyika hadi uhuru na kuendelea kuwa mstari wa mbele wa Muungano.",
    ),
    (
        ("karume", "abeid"),
        "Sheikh Abeid Amani Karume aliongoza mapinduzi ya Zanzibar na kuwa Makamu wa Rais wa kwanza wa Muungano.",
    ),
    (
        ("jwtz", "jeshi", "wananchi"),
        "Jeshi la Wananchi wa Tanzania (JWTZ) lina historia ya ulinzi wa taifa tangu miaka ya 1960.",
    ),
    (
        ("uzalendo", "patriot"),
        "Uzalendo ni upendo wa taifa — kujifunza historia, kuheshimu nembo, na kuungana na vijana wengine katika Muungano.",
    ),
    (
        ("baraza", "visiwani", "zanzibar", "pembe"),
        "Bara na Visiwani ni pande mbili za taifa moja — Muungano unawapa nafasi ya kukutana na kujenga uhusiano wa kweli.",
    ),
    (
        ("cheti", "certificate", "qr"),
        "Cheti cha Balozi wa Muungano kinathibitishwa kwa QR na kinaweza kuwekwa kwenye CV yako.",
    ),
    (
        ("help", "msaada", "menyu", "menu"),
        "Niulize kuhusu: Muungano 1964, Nyerere, Karume, JWTZ, Uzalendo, Bara na Visiwani, au Cheti cha QR.",
    ),
]


def tutor_reply(message: str) -> dict:
    text = (message or "").strip().lower()
    if not text:
        return {
            "reply": (
                "Habari Mzalendo! Mimi ni Mwalimu wa Kivuko — msaidizi wako wa historia ya Muungano. "
                "Uliza kuhusu Muungano 1964, Nyerere, Karume, JWTZ, au Uzalendo."
            ),
            "suggestions": ["Muungano 1964", "Nyerere", "Karume", "Uzalendo", "Cheti QR"],
        }

    for keywords, answer in TUTOR_KB:
        if any(kw in text for kw in keywords):
            return {
                "reply": answer,
                "suggestions": ["Muungano 1964", "JWTZ", "Uzalendo", "Bara na Visiwani"],
            }

    return {
        "reply": (
            "Samahani, bado najifunza swali hilo. Jaribu: 'Muungano 1964', 'Nyerere', 'Karume', "
            "'JWTZ', 'Uzalendo', au 'Cheti QR'."
        ),
        "suggestions": ["Muungano 1964", "Nyerere", "Karume", "Uzalendo"],
    }
