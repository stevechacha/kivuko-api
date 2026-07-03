import base64
import io

import qrcode
from django.conf import settings


def build_verify_url(cert_code: str) -> str:
    base = getattr(settings, "PUBLIC_APP_BASE_URL", "http://localhost:8081").rstrip("/")
    return f"{base}/thibitisha/{cert_code}"


def qr_data_url(text: str, box_size: int = 6) -> str:
    qr = qrcode.QRCode(box_size=box_size, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
