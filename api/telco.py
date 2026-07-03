"""Africa's Talking SMS / airtime integration with sandbox fallback."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


def normalize_tz_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("255"):
        return f"+{digits}"
    if digits.startswith("0"):
        return f"+255{digits[1:]}"
    if len(digits) == 9:
        return f"+255{digits}"
    return f"+{digits}" if digits else ""


def _at_configured() -> bool:
    return bool(getattr(settings, "AFRICASTALKING_USERNAME", "") and getattr(settings, "AFRICASTALKING_API_KEY", ""))


def _at_base_url() -> str:
    if getattr(settings, "AFRICASTALKING_SANDBOX", True):
        return "https://api.sandbox.africastalking.com"
    return "https://api.africastalking.com"


def _at_request(path: str, form: dict) -> dict:
    username = settings.AFRICASTALKING_USERNAME
    api_key = settings.AFRICASTALKING_API_KEY
    data = urllib.parse.urlencode({**form, "username": username}).encode()
    req = urllib.request.Request(
        f"{_at_base_url()}{path}",
        data=data,
        headers={"apiKey": api_key, "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode() if exc.fp else str(exc)
        logger.warning("Africa's Talking HTTP error: %s %s", exc.code, body)
        return {"error": body, "status": "failed"}
    except Exception as exc:
        logger.warning("Africa's Talking request failed: %s", exc)
        return {"error": str(exc), "status": "failed"}


def send_sms(phone: str, message: str) -> dict:
    """Send SMS via Africa's Talking or record sandbox delivery."""
    normalized = normalize_tz_phone(phone)
    if not normalized:
        return {"status": "failed", "detail": "Invalid phone number"}

    if not _at_configured():
        ref = f"SMS-SBX-{timezone.now().strftime('%H%M%S')}"
        logger.info("SMS sandbox → %s: %s", normalized, message[:80])
        return {
            "status": "sandbox",
            "reference": ref,
            "phone": normalized,
            "message": message,
            "provider": "sandbox",
        }

    payload = _at_request(
        "/version1/messaging",
        {
            "to": normalized,
            "message": message,
            "from": getattr(settings, "SMS_SENDER_ID", "KIVUKO"),
        },
    )
    recipients = (payload.get("SMSMessageData") or {}).get("Recipients") or []
    if recipients:
        rec = recipients[0]
        return {
            "status": rec.get("status", "sent").lower(),
            "reference": rec.get("messageId", ""),
            "phone": normalized,
            "provider": "africastalking",
            "raw": payload,
        }
    return {
        "status": "failed",
        "phone": normalized,
        "provider": "africastalking",
        "raw": payload,
    }


def disburse_airtime(phone: str, amount_tzs: int) -> dict:
    """Disburse airtime via Africa's Talking or sandbox reference."""
    normalized = normalize_tz_phone(phone)
    if not normalized:
        return {"status": "failed", "detail": "Invalid phone number"}

    if not _at_configured():
        ref = f"AT-SBX-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        logger.info("Airtime sandbox TZS %s → %s ref %s", amount_tzs, normalized, ref)
        return {
            "status": "sandbox",
            "reference": ref,
            "phone": normalized,
            "amount_tzs": amount_tzs,
            "provider": "sandbox",
        }

    payload = _at_request(
        "/version1/airtime/send",
        {
            "recipients": json.dumps([{"phoneNumber": normalized, "amount": f"TZS {amount_tzs}"}]),
        },
    )
    responses = (payload.get("responses") or [{}])
    first = responses[0] if responses else {}
    status = (first.get("status") or "failed").lower()
    return {
        "status": "sent" if status == "sent" else status,
        "reference": first.get("requestId") or first.get("transactionId") or "",
        "phone": normalized,
        "amount_tzs": amount_tzs,
        "provider": "africastalking",
        "raw": payload,
    }


def notify_match_sms(participant, peer) -> list[dict]:
    """SMS both youth when a cross-island match is created (Tier 2)."""
    if not getattr(settings, "SMS_MATCH_NOTIFICATIONS", True):
        return []
    app_url = getattr(settings, "PUBLIC_APP_BASE_URL", "")
    results = []
    for user, other in ((participant, peer), (peer, participant)):
        if user.is_seed_peer or not user.phone:
            continue
        region = other.region_label or other.home_area
        msg = (
            f"Habari {user.name.split()[0]}! Umeoanishwa na {other.name.split()[0]} kutoka {region} "
            f"kwenye Kivuko la Muungano Hub. Fungua {app_url}/dhamira kuanza Dhamira ya pamoja."
        )
        results.append(send_sms(user.phone, msg))
    return results


def send_whatsapp_reply(to_phone: str, text: str) -> dict:
    """Outbound WhatsApp via Meta Graph API when configured."""
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
    phone_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    if not token or not phone_id:
        return {"status": "sandbox", "detail": "WhatsApp API not configured"}

    digits = re.sub(r"\D", "", to_phone)
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": digits,
            "type": "text",
            "text": {"body": text[:4096]},
        }
    ).encode()
    req = urllib.request.Request(
        f"https://graph.facebook.com/v19.0/{phone_id}/messages",
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            return {"status": "sent", "provider": "meta", "raw": data}
    except Exception as exc:
        logger.warning("WhatsApp send failed: %s", exc)
        return {"status": "failed", "detail": str(exc)}
