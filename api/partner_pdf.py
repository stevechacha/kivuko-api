"""Partner impact report PDF (Tier 2)."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def build_partner_report_pdf(stats: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFillColor(colors.HexColor("#0B3D2E"))
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, height - 25 * mm, "Kivuko la Muungano Hub — Partner Report")

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 32 * mm, f"Generated: {stats.get('generated_at', '')}")

    y = height - 45 * mm
    lines = [
        ("Youth registered", stats.get("youth_registered", 0)),
        ("Pairs today", stats.get("pairs_today", 0)),
        ("Certificates issued", stats.get("certificates_issued", 0)),
        ("Completed missions", stats.get("completed_missions", 0)),
        ("Mainland youth", stats.get("bara_youth", 0)),
        ("Islands youth", stats.get("visiwani_youth", 0)),
        ("Active regions", stats.get("regions_active", 0)),
        ("Elder radio nominees", stats.get("elder_radio_nominees", 0)),
        ("AUTO flags pending", stats.get("auto_flagged_pending", 0)),
        ("Rewards pending (TZS)", stats.get("rewards_pending_tzs", 0)),
    ]
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "National reach summary")
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    for label, value in lines:
        c.drawString(25 * mm, y, f"• {label}: {value}")
        y -= 7 * mm

    institutions = stats.get("institutions") or []
    if institutions:
        y -= 5 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Institution cohorts")
        y -= 8 * mm
        c.setFont("Helvetica", 10)
        for inst in institutions[:12]:
            c.drawString(
                25 * mm,
                y,
                f"• {inst.get('code')} — {inst.get('name')}: {inst.get('youth_count', 0)} youth",
            )
            y -= 6 * mm
            if y < 30 * mm:
                c.showPage()
                y = height - 25 * mm

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(20 * mm, 15 * mm, "Sisi kwa Sisi — Bara na Visiwani, Kizazi Kimoja, Taifa Moja.")
    c.showPage()
    c.save()
    return buffer.getvalue()
