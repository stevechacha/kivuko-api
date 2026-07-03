"""Additional API views for proposal gap features."""

from __future__ import annotations

import secrets

from django.conf import settings
from django.db.models import Avg, Count, Sum
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.cert_pdf import build_certificate_pdf
from api.grades import patriotism_grade
from api.models import (
    Certificate,
    ContentReport,
    ElderRadioNominee,
    ElderStory,
    GalaNominee,
    Institution,
    MapConnection,
    Match,
    Mission,
    Participant,
    Region,
    RewardDisbursement,
)
from api.serializers import (
    CertificateSerializer,
    ElderRadioEntrySerializer,
    ElderStoryResolveSerializer,
    ElderStorySerializer,
    ElderStorySubmitSerializer,
    GalaCeremonySerializer,
    InstitutionSerializer,
    PartnerDashboardSerializer,
    RadioPartnerSerializer,
    RewardDisbursementSerializer,
    RewardDisburseSerializer,
    RadioBroadcastScriptSerializer,
    UserRewardSerializer,
)
from api.views import (
    _report_time_label,
    _require_admin_key,
    _whatsapp_bot_reply,
)


def _serialize_elder_story(story: ElderStory) -> dict:
    return {
        "id": story.id,
        "contributor_name": story.contributor_name,
        "title": story.title,
        "body": story.body,
        "home_area": story.home_area,
        "region": story.region,
        "region_label": "Zanzibar" if story.region == Region.VISIWANI else "Mainland",
        "audio_url": story.audio_url,
        "video_url": story.video_url,
        "status": story.status,
        "radio_nominated": hasattr(story, "radio_nomination"),
        "created_at_label": _report_time_label(story.created_at),
    }


class InstitutionsListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        code = request.query_params.get("code", "").strip().upper()
        qs = Institution.objects.all()
        if code:
            qs = qs.filter(code=code)
        return Response(InstitutionSerializer(qs, many=True).data)


class ElderStorySubmitView(APIView):
    def post(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)

        serializer = ElderStorySubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        story = ElderStory.objects.create(
            contributor_name=data.get("contributor_name") or participant.name,
            contributor_phone=data.get("contributor_phone", participant.phone),
            home_area=data.get("home_area") or participant.home_area,
            region=data.get("region") or participant.region,
            title=data["title"].strip(),
            body=data["body"].strip(),
            audio_url=data.get("audio_url", ""),
            video_url=data.get("video_url", ""),
            status=ElderStory.Status.PENDING,
        )
        return Response(ElderStorySerializer(_serialize_elder_story(story)).data, status=201)


class ElderStoriesPublicView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        stories = ElderStory.objects.filter(status=ElderStory.Status.APPROVED).order_by("-created_at")[:30]
        return Response(ElderStorySerializer([_serialize_elder_story(s) for s in stories], many=True).data)


def _elder_radio_entries() -> list[dict]:
    nominees = (
        ElderRadioNominee.objects.select_related("story")
        .filter(story__status=ElderStory.Status.APPROVED)
        .order_by("-added_at")[:10]
    )
    entries = []
    for i, nom in enumerate(nominees, start=1):
        story = nom.story
        entries.append(
            {
                "rank": i,
                "story_id": story.id,
                "contributor_name": story.contributor_name,
                "title": story.title,
                "home_area": story.home_area,
                "region_label": "Zanzibar" if story.region == Region.VISIWANI else "Mainland",
                "audio_url": story.audio_url,
            }
        )
    return entries


def _build_radio_scripts(entries: list[dict]) -> tuple[str, str]:
    sw_lines = [
        "SEGMENT: Kivuko la Muungano Hub — Wazee Top 10",
        "Kila mwaka, hadithi za wazee zinazoidhinishwa zinatambuliwa kwenye redio ya taifa.",
        "",
    ]
    en_lines = [
        "SEGMENT: Union Bridge Hub — Elder Top 10",
        "Each year, approved elder oral histories are honoured on national radio.",
        "",
    ]
    for entry in entries:
        sw_lines.append(
            f"{entry['rank']}. {entry['contributor_name']} — {entry['home_area']} ({entry['region_label']})"
        )
        sw_lines.append(f"   \"{entry['title']}\"")
        sw_lines.append("")
        en_lines.append(
            f"{entry['rank']}. {entry['contributor_name']} — {entry['home_area']} ({entry['region_label']})"
        )
        en_lines.append(f"   \"{entry['title']}\"")
        en_lines.append("")
    sw_lines.append("Asante. Sisi kwa Sisi — Bara na Visiwani, Kizazi Kimoja, Taifa Moja.")
    en_lines.append("Thank you. Us for us — Mainland and Isles, One Generation, One Nation.")
    return "\n".join(sw_lines), "\n".join(en_lines)


class ElderRadioTop10View(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        entries = _elder_radio_entries()
        return Response(ElderRadioEntrySerializer(entries, many=True).data)


class RadioBroadcastScriptView(APIView):
    """Copy-ready radio segment script for broadcast partners."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        entries = _elder_radio_entries()
        script_sw, script_en = _build_radio_scripts(entries)
        return Response(
            RadioBroadcastScriptSerializer(
                {
                    "station_name": "Radio Taifa — Muungano Segment",
                    "segment_title": "Top 10 Elder Contributors",
                    "broadcast_ready": len(entries) >= 3,
                    "script_sw": script_sw,
                    "script_en": script_en,
                    "nominees": entries,
                }
            ).data
        )


class MyRewardsView(APIView):
    """Youth-facing micro-reward ledger (airtime / M-Pesa sandbox)."""

    def get(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)

        rewards = RewardDisbursement.objects.filter(participant=participant).order_by("-created_at")[:20]
        payload = [
            {
                "id": r.id,
                "amount_tzs": r.amount_tzs,
                "reward_type": r.reward_type,
                "status": r.status,
                "source": r.source or "Mission reward",
                "created_at_label": _report_time_label(r.created_at),
            }
            for r in rewards
        ]
        pending_total = (
            RewardDisbursement.objects.filter(
                participant=participant,
                status=RewardDisbursement.Status.PENDING,
            ).aggregate(total=Sum("amount_tzs"))["total"]
            or 0
        )
        return Response(
            {
                "rewards": UserRewardSerializer(payload, many=True).data,
                "pending_total_tzs": pending_total,
                "sent_total_tzs": (
                    RewardDisbursement.objects.filter(
                        participant=participant,
                        status=RewardDisbursement.Status.SENT,
                    ).aggregate(total=Sum("amount_tzs"))["total"]
                    or 0
                ),
            }
        )


class AdminElderStoriesView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        denied = _require_admin_key(request)
        if denied:
            return denied
        status_filter = request.query_params.get("status", "pending")
        if status_filter not in ("pending", "approved", "rejected"):
            status_filter = "pending"
        stories = ElderStory.objects.filter(status=status_filter).order_by("-created_at")[:50]
        return Response(ElderStorySerializer([_serialize_elder_story(s) for s in stories], many=True).data)


class AdminElderStoryResolveView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, story_id):
        denied = _require_admin_key(request)
        if denied:
            return denied
        serializer = ElderStoryResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        try:
            story = ElderStory.objects.get(id=story_id, status=ElderStory.Status.PENDING)
        except ElderStory.DoesNotExist:
            return Response({"detail": "Story not found or already reviewed."}, status=404)

        story.status = ElderStory.Status.APPROVED if action == "approve" else ElderStory.Status.REJECTED
        story.reviewed_at = timezone.now()
        story.save(update_fields=["status", "reviewed_at"])
        return Response(ElderStorySerializer(_serialize_elder_story(story)).data)


class AdminElderRadioToggleView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, story_id):
        denied = _require_admin_key(request)
        if denied:
            return denied
        nominated = bool(request.data.get("nominated", True))
        try:
            story = ElderStory.objects.get(id=story_id, status=ElderStory.Status.APPROVED)
        except ElderStory.DoesNotExist:
            return Response({"detail": "Approved elder story not found."}, status=404)

        if nominated:
            if ElderRadioNominee.objects.count() >= 10 and not hasattr(story, "radio_nomination"):
                return Response({"detail": "Top 10 elder radio list is full."}, status=400)
            ElderRadioNominee.objects.get_or_create(story=story)
        else:
            ElderRadioNominee.objects.filter(story=story).delete()

        story.refresh_from_db()
        return Response(ElderStorySerializer(_serialize_elder_story(story)).data)


class CertificateListView(APIView):
    def get(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)
        certs = Certificate.objects.filter(participant=participant).select_related("mission").order_by("-issued_at")
        return Response(CertificateSerializer(certs, many=True).data)


class CertificatePdfView(APIView):
    def get(self, request, cert_code):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)
        try:
            cert = Certificate.objects.select_related("participant").get(
                cert_code=cert_code, participant=participant
            )
        except Certificate.DoesNotExist:
            return Response({"detail": "Certificate not found."}, status=404)

        pdf_bytes = build_certificate_pdf(cert)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{cert.cert_code}.pdf"'
        return response


class PartnerDashboardView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        denied = _require_admin_key(request)
        if denied:
            return denied

        today = timezone.localdate()
        region_counts = (
            Participant.objects.filter(is_seed_peer=False)
            .values("region")
            .annotate(count=Count("id"))
        )
        bara = next((r["count"] for r in region_counts if r["region"] == Region.BARA), 0)
        visiwani = next((r["count"] for r in region_counts if r["region"] == Region.VISIWANI), 0)

        institutions = []
        for inst in Institution.objects.annotate(youth_count=Count("participants")).order_by("-youth_count")[:12]:
            institutions.append(
                {
                    "code": inst.code,
                    "name": inst.name,
                    "home_area": inst.home_area,
                    "region": inst.region,
                    "youth_count": inst.youth_count,
                }
            )

        recent_certs = [
            {
                "cert_code": c.cert_code,
                "user_name": c.participant.name,
                "issued_date": c.issued_at.strftime("%d/%m/%Y"),
            }
            for c in Certificate.objects.select_related("participant").order_by("-issued_at")[:5]
        ]

        return Response(
            PartnerDashboardSerializer(
                {
                    "youth_registered": Participant.objects.filter(is_seed_peer=False).count(),
                    "pairs_today": Match.objects.filter(created_at__date=today).count(),
                    "certificates_issued": Certificate.objects.count(),
                    "completed_missions": Mission.objects.filter(status="completed").count(),
                    "bara_youth": bara,
                    "visiwani_youth": visiwani,
                    "regions_active": MapConnection.objects.values("from_region").distinct().count(),
                    "institutions": institutions,
                    "pending_elder_stories": ElderStory.objects.filter(status=ElderStory.Status.PENDING).count(),
                    "elder_radio_nominees": ElderRadioNominee.objects.count(),
                    "auto_flagged_pending": ContentReport.objects.filter(
                        status=ContentReport.Status.PENDING,
                        auto_flagged=True,
                    ).count(),
                    "rewards_pending_tzs": RewardDisbursement.objects.filter(
                        status=RewardDisbursement.Status.PENDING
                    ).aggregate(total=Sum("amount_tzs"))["total"]
                    or 0,
                    "recent_certificates": recent_certs,
                }
            ).data
        )


class RadioPartnerView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        denied = _require_admin_key(request)
        if denied:
            return denied

        elder_top = ElderRadioTop10View().get(request).data
        youth_gala = []
        nominees = GalaNominee.objects.select_related("participant").order_by("-created_at")[:10]
        for i, nom in enumerate(nominees, start=1):
            p = nom.participant
            youth_gala.append(
                {
                    "rank": i,
                    "name": p.name,
                    "home_area": p.home_area,
                    "region_label": p.region_label,
                    "patriotism_points": p.patriotism_points,
                }
            )

        return Response(
            RadioPartnerSerializer(
                {
                    "station_name": "Radio Tanzania — Muungano Segment",
                    "segment_title": "Top 10 Wazee + Vijana Gala",
                    "elder_nominees": elder_top,
                    "youth_gala_nominees": youth_gala,
                    "approved_elder_stories": ElderStory.objects.filter(
                        status=ElderStory.Status.APPROVED
                    ).count(),
                    "broadcast_ready": len(elder_top) > 0 or len(youth_gala) > 0,
                }
            ).data
        )


class GalaCeremonyView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        youth = []
        leaders = Participant.objects.filter(is_seed_peer=False).order_by("-patriotism_points")[:10]
        nominee_ids = set(GalaNominee.objects.values_list("participant_id", flat=True))
        for i, p in enumerate(leaders, start=1):
            youth.append(
                {
                    "rank": i,
                    "name": p.name,
                    "home_area": p.home_area,
                    "region_label": p.region_label,
                    "patriotism_points": p.patriotism_points,
                    "grade": patriotism_grade(p.patriotism_points),
                    "gala_nominated": p.id in nominee_ids,
                }
            )

        elders = ElderRadioTop10View().get(request).data
        avg_score = (
            Participant.objects.filter(is_seed_peer=False).aggregate(avg=Avg("patriotism_points"))["avg"] or 0
        )

        return Response(
            GalaCeremonySerializer(
                {
                    "event_title": "Gala ya Muungano na Uzalendo 2026",
                    "live_mode": True,
                    "youth_finalists": youth,
                    "elder_finalists": elders,
                    "total_certificates": Certificate.objects.count(),
                    "total_connections": MapConnection.objects.count(),
                    "average_patriotism_score": int(avg_score),
                    "ceremony_message": "Hongera kwa vijana na wazee wote waliojenga daraja la Muungano!",
                }
            ).data
        )


class AdminRewardsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        denied = _require_admin_key(request)
        if denied:
            return denied
        status_filter = request.query_params.get("status", "pending")
        qs = RewardDisbursement.objects.select_related("participant").order_by("-created_at")
        if status_filter in ("pending", "processing", "sent", "failed"):
            qs = qs.filter(status=status_filter)
        return Response(
            RewardDisbursementSerializer(
                [
                    {
                        "id": r.id,
                        "participant_name": r.participant.name,
                        "participant_phone": r.participant.phone,
                        "amount_tzs": r.amount_tzs,
                        "reward_type": r.reward_type,
                        "status": r.status,
                        "source": r.source,
                        "reference": r.reference,
                        "created_at_label": _report_time_label(r.created_at),
                    }
                    for r in qs[:50]
                ],
                many=True,
            ).data
        )


class AdminRewardDisburseView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, reward_id):
        denied = _require_admin_key(request)
        if denied:
            return denied
        serializer = RewardDisburseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        try:
            reward = RewardDisbursement.objects.select_related("participant").get(id=reward_id)
        except RewardDisbursement.DoesNotExist:
            return Response({"detail": "Reward not found."}, status=404)

        if action == "send":
            reward.status = RewardDisbursement.Status.SENT
            reward.reference = reward.reference or f"KMH-{secrets.token_hex(4).upper()}"
            reward.sent_at = timezone.now()
        elif action == "fail":
            reward.status = RewardDisbursement.Status.FAILED
        else:
            reward.status = RewardDisbursement.Status.PROCESSING

        reward.save(update_fields=["status", "reference", "sent_at"])
        return Response(
            RewardDisbursementSerializer(
                {
                    "id": reward.id,
                    "participant_name": reward.participant.name,
                    "participant_phone": reward.participant.phone,
                    "amount_tzs": reward.amount_tzs,
                    "reward_type": reward.reward_type,
                    "status": reward.status,
                    "source": reward.source,
                    "reference": reward.reference,
                    "created_at_label": _report_time_label(reward.created_at),
                }
            ).data
        )


class WhatsAppWebhookView(APIView):
    """Meta WhatsApp Business API webhook (verify + inbound messages)."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")
        verify_token = getattr(settings, "WHATSAPP_VERIFY_TOKEN", "MUUNGANO2026")
        if mode == "subscribe" and token == verify_token and challenge:
            return HttpResponse(challenge, content_type="text/plain")
        return Response({"detail": "Verification failed."}, status=403)

    def post(self, request):
        payload = request.data
        entries = payload.get("entry") or []
        replies = []
        for entry in entries:
            for change in entry.get("changes") or []:
                value = change.get("value") or {}
                for message in value.get("messages") or []:
                    text = ""
                    if message.get("type") == "text":
                        text = (message.get("text") or {}).get("body", "")
                    session_id = message.get("from", "")
                    if text:
                        bot = _whatsapp_bot_reply(text, session_id)
                        replies.append(bot)
        return Response({"status": "ok", "replies": replies})


class UssdGatewayView(APIView):
    """Telco USSD gateway format (Africa's Talking / generic)."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from api.ussd_bot import handle_ussd_message

        session_id = (
            request.data.get("sessionId")
            or request.data.get("session_id")
            or request.POST.get("sessionId")
            or ""
        ).strip()
        text = (
            request.data.get("text")
            or request.POST.get("text")
            or ""
        ).strip()
        phone = (
            request.data.get("phoneNumber")
            or request.data.get("phone")
            or request.POST.get("phoneNumber")
            or ""
        ).strip()

        result = handle_ussd_message(text, session_id or None)
        lines = result.get("lines") or ["Karibu Kivuko Hub"]
        suggestions = result.get("suggestions") or []
        is_menu = bool(suggestions) and not text.strip()
        prefix = "CON" if is_menu else "END"
        body = f"{prefix} " + "\n".join(lines[:8])

        response = HttpResponse(body, content_type="text/plain")
        if phone:
            response["X-USSD-Phone"] = phone
        return response
