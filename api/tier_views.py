"""Tier 1–3 feature API views."""

from __future__ import annotations

from django.conf import settings
from django.db.models import Avg, Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.ai_tutor import tutor_reply
from api.grades import patriotism_grade
from api.models import (
    Certificate,
    ContentReport,
    ElderRadioNominee,
    Institution,
    MapConnection,
    Match,
    Mission,
    Participant,
    Region,
    RewardDisbursement,
)
from api.partner_pdf import build_partner_report_pdf
from api.serializers import (
    AiTutorSerializer,
    InstitutionStatsSerializer,
    PlatformBrandingSerializer,
)
from api.telco import _at_configured
from api.views import _require_admin_key


def _partner_stats_payload() -> dict:
    today = timezone.localdate()
    youth = Participant.objects.filter(is_seed_peer=False)
    institutions = []
    for inst in Institution.objects.annotate(youth_count=Count("participants")).order_by("-youth_count"):
        institutions.append(
            {
                "code": inst.code,
                "name": inst.name,
                "home_area": inst.home_area,
                "region": inst.region,
                "youth_count": inst.youth_count,
            }
        )
    return {
        "generated_at": timezone.now().strftime("%d %B %Y %H:%M"),
        "youth_registered": youth.count(),
        "pairs_today": Match.objects.filter(created_at__date=today).count(),
        "certificates_issued": Certificate.objects.count(),
        "completed_missions": MapConnection.objects.count(),
        "bara_youth": youth.filter(region=Region.BARA).count(),
        "visiwani_youth": youth.filter(region=Region.VISIWANI).count(),
        "regions_active": youth.values("home_area").distinct().count(),
        "elder_radio_nominees": ElderRadioNominee.objects.count(),
        "auto_flagged_pending": ContentReport.objects.filter(
            status=ContentReport.Status.PENDING,
            auto_flagged=True,
        ).count(),
        "rewards_pending_tzs": RewardDisbursement.objects.filter(
            status=RewardDisbursement.Status.PENDING
        ).aggregate(total=Sum("amount_tzs"))["total"]
        or 0,
        "institutions": institutions,
    }


class PlatformBrandingView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        ministry = request.query_params.get("ministry", "").lower() in ("1", "true", "yes")
        ministry_mode = ministry or getattr(settings, "MINISTRY_MODE", False)
        return Response(
            PlatformBrandingSerializer(
                {
                    "ministry_mode": ministry_mode,
                    "program_name": "Elimu ya Muungano",
                    "program_name_en": "Union Education Innovation",
                    "tagline_sw": "Sisi kwa Sisi — Bara na Visiwani, Kizazi Kimoja, Taifa Moja.",
                    "tagline_en": "Us for us — Mainland and Isles, One Generation, One Nation.",
                    "ussd_shortcode": getattr(settings, "USSD_SHORTCODE", "*149*88#"),
                    "sms_shortcode": getattr(settings, "SMS_SHORTCODE", "15064"),
                    "sms_keyword": getattr(settings, "SMS_KEYWORD", "MUUNGANO"),
                    "live_stream_url": getattr(settings, "LIVE_STREAM_URL", ""),
                    "whatsapp_display": getattr(settings, "WHATSAPP_DISPLAY_NUMBER", "+255 000 000 000"),
                    "telco_configured": _at_configured(),
                    "auto_disburse_rewards": getattr(settings, "AUTO_DISBURSE_REWARDS", False),
                }
            ).data
        )


class InstitutionStatsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, code):
        inst = Institution.objects.filter(code=code.strip().upper()).first()
        if not inst:
            return Response({"detail": "Institution not found."}, status=404)

        youth = Participant.objects.filter(institution=inst, is_seed_peer=False)
        leaders = []
        for i, p in enumerate(youth.order_by("-patriotism_points")[:10], start=1):
            leaders.append(
                {
                    "rank": i,
                    "name": p.name,
                    "home_area": p.home_area,
                    "region_label": p.region_label,
                    "patriotism_points": p.patriotism_points,
                    "grade": patriotism_grade(p.patriotism_points),
                }
            )

        return Response(
            InstitutionStatsSerializer(
                {
                    "code": inst.code,
                    "name": inst.name,
                    "home_area": inst.home_area,
                    "region": inst.region,
                    "region_label": "Zanzibar" if inst.region == Region.VISIWANI else "Mainland",
                    "youth_count": youth.count(),
                    "pairs_active": Match.objects.filter(
                        participant__institution=inst,
                        status="active",
                    ).count()
                    + Match.objects.filter(peer__institution=inst, status="active").count(),
                    "certificates": Certificate.objects.filter(participant__institution=inst).count(),
                    "leaderboard": leaders,
                }
            ).data
        )


class PartnerReportPdfView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        denied = _require_admin_key(request)
        if denied:
            return denied
        stats = _partner_stats_payload()
        pdf = build_partner_report_pdf(stats)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="muungano-partner-report.pdf"'
        return response


class AiTutorView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        result = tutor_reply(message)
        return Response(AiTutorSerializer(result).data)


class Phase2RoadmapView(APIView):
    """Tier 3 deferred features — documented for judges."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(
            {
                "phase": 2,
                "deferred_features": [
                    {"id": "native_android", "title": "Native Android app (Play Store)", "status": "planned"},
                    {"id": "nida_verify", "title": "NIDA / school ID verification", "status": "planned"},
                    {"id": "blockchain_certs", "title": "Blockchain certificate anchoring", "status": "not_planned"},
                    {"id": "youth_wings", "title": "Regional youth wing integrations", "status": "planned"},
                    {"id": "hybrid_gala", "title": "In-person Gala hybrid events", "status": "planned"},
                ],
                "live_now": [
                    "Web PWA",
                    "WhatsApp bot + webhook",
                    "USSD gateway",
                    "QR certificates",
                    "Live Union Map",
                    "AI Kiswahili tutor (rule-based)",
                ],
            }
        )
