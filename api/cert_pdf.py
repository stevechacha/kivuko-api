"""Generate downloadable PDF certificates."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from api.models import Certificate
from api.utils import build_verify_url


def build_certificate_pdf(cert: Certificate) -> bytes:
    buffer = BytesIO()
    page = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=page)
    width, height = page

    c.setFillColor(colors.HexColor("#0B3D2E"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    c.setStrokeColor(colors.HexColor("#F1C40F"))
    c.setLineWidth(3)
    c.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm, fill=0, stroke=1)

    c.setFillColor(colors.HexColor("#F1C40F"))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 28 * mm, "KIVUKO LA MUUNGANO HUB")

    c.setFillColor(colors.white)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 38 * mm, "Cheti cha Uzalendo — Union Bridge Certificate")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 55 * mm, cert.participant.name)

    c.setFont("Helvetica", 11)
    c.drawCentredString(
        width / 2,
        height - 65 * mm,
        f"Amekamilisha Dhamira ya Muungano · {cert.participant.home_area}",
    )

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 78 * mm, cert.cert_code)

    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, height - 86 * mm, f"Issued {cert.issued_at.strftime('%d %B %Y')}")

    verify_url = build_verify_url(cert.cert_code)
    c.setFont("Helvetica", 9)
    c.drawCentredString(width / 2, 22 * mm, f"Verify: {verify_url}")

    c.showPage()
    c.save()
    return buffer.getvalue()
