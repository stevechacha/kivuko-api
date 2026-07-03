from datetime import timedelta
import random

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import (
    AcademyArticle,
    Certificate,
    ChatMessage,
    ContentReport,
    ElderAudio,
    MapConnection,
    Match,
    Mission,
    MissionStepProgress,
    Participant,
    QuizQuestion,
    QuizSubmission,
    Region,
    TimelineEvent,
)
from api.serializers import (
    AcademyArticleSerializer,
    AdminDashboardSerializer,
    CertificateSerializer,
    ChatMessageSerializer,
    ChatThreadSerializer,
    ChemshaBongoResultSerializer,
    ChemshaBongoSubmitSerializer,
    ElderAudioSerializer,
    LeaderboardEntrySerializer,
    LiveImpactSerializer,
    MapStatsSerializer,
    MatchResultSerializer,
    MissionCompleteSerializer,
    ParticipantSerializer,
    QuizQuestionSerializer,
    QuizSubmitSerializer,
    LoginSerializer,
    RegisterSerializer,
    ReportCreateSerializer,
    ReportedItemSerializer,
    ReportResolveSerializer,
    SendMessageSerializer,
    SessionSerializer,
    TimelineEventSerializer,
)
from api.progress import build_mission_progress, mark_step_complete
from api.grades import patriotism_grade, MISSION_STEPS
from api.utils import build_verify_url, qr_data_url


def _normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def _session_payload(participant: Participant, message: str | None = None) -> dict:
    active = (
        Match.objects.filter(participant=participant, status="active")
        .select_related("mission")
        .order_by("-created_at")
        .first()
    )
    active_mission_id = None
    active_match_id = None
    if active:
        active_match_id = active.id
        try:
            active_mission_id = active.mission.id
        except Mission.DoesNotExist:
            active_mission_id = None

    payload = {
        "participant": participant,
        "active_mission_id": active_mission_id,
        "active_match_id": active_match_id,
    }
    if message:
        payload["message"] = message
    return payload

STATUS_MESSAGES = [
    "Inatafuta wanachama Visiwani…",
    "Inalinganisha maslahi ya kihistoria…",
    "Inathibitisha muunganiko wa kivuko…",
]

PEER_REPLIES = [
    "Vizuri sana! 🙌",
    "Nakubaliana nawe.",
    "Hii ni sehemu yangu pendwa ya historia yetu!",
    "Sawa kabisa — tuendelee pamoja.",
    "Hongera kwa ujasiri wako wa kujifunza historia ya taifa!",
]


def _peer_reply_text(user_text: str) -> str:
    lowered = user_text.lower()
    if any(w in lowered for w in ("1964", "muungano", "union", "april", "aprili")):
        return "Ndio! 26 Aprili 1964 — siku muhimu kwa taifa letu. 🇹🇿"
    if any(w in lowered for w in ("habari", "mambo", "salamu", "hello", "hi")):
        return "Marahaba! Niko tayari kwa dhamira yetu ya pamoja 😊"
    if any(w in lowered for w in ("asante", "thanks", "shukrani")):
        return "Karibu sana! Muungano ni nguvu yetu pamoja. 💪"
    if any(w in lowered for w in ("nyerere", "karume", "wazee", "baba")):
        return "Wazee wetu walituacha urithi wa umoja — tuendelee kuheshimu. 🙏"
    if "?" in user_text:
        return "Swali zuri! Hebu tujaribu kujibu pamoja kwenye jaribio. 📝"
    return random.choice(PEER_REPLIES)


def _mission_peer(mission: Mission, participant: Participant) -> Participant:
    match = mission.match
    return match.peer if match.participant_id == participant.id else match.participant


def _visible_messages(mission: Mission):
    now = timezone.now()
    return mission.messages.filter(Q(deliver_at__isnull=True) | Q(deliver_at__lte=now))


def _opposite_region(region: str) -> str:
    return Region.VISIWANI if region == Region.BARA else Region.BARA


def _find_peer(participant: Participant) -> Participant:
    opposite = _opposite_region(participant.region)
    waiting = (
        Participant.objects.filter(region=opposite, is_seed_peer=False)
        .exclude(id=participant.id)
        .exclude(matches_as_participant__status="active")
        .first()
    )
    if waiting:
        return waiting
    seed = Participant.objects.filter(region=opposite, is_seed_peer=True).first()
    if seed:
        return seed
    return Participant.objects.create(
        name="Khadija Mrisho",
        phone="0700 000 001",
        college="Chuo cha Zanzibar",
        home_area="Unguja",
        region=Region.VISIWANI,
        is_seed_peer=True,
    )


def _seed_chat(mission: Mission, participant: Participant, peer: Participant) -> None:
    if mission.messages.exists():
        return
    ChatMessage.objects.bulk_create(
        [
            ChatMessage(
                mission=mission,
                from_role="system",
                text=f"Umeunganishwa na {peer.name.split()[0]} — {peer.region_label} 🌊",
            ),
            ChatMessage(
                mission=mission,
                sender=peer,
                from_role="peer",
                text="Habari! Niko tayari kwa Dhamira ya leo 😊",
            ),
            ChatMessage(
                mission=mission,
                sender=participant,
                from_role="me",
                text=f"Habari {peer.name.split()[0]}! Nami niko tayari — tuanze na jaribio?",
            ),
            ChatMessage(
                mission=mission,
                sender=peer,
                from_role="peer",
                text="Sawa! Muungano ulianzishwa mwaka gani, nadhani unajua 😉",
            ),
        ]
    )


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not data.get("accepted_terms"):
            return Response(
                {"detail": "Lazima ukubali masharti ya uoanishaji na usalama."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        phone_key = _normalize_phone(data["phone"])
        existing = (
            Participant.objects.filter(is_seed_peer=False)
            .order_by("-created_at")
        )
        for p in existing:
            if _normalize_phone(p.phone) == phone_key:
                return Response(
                    {
                        "detail": "Namba hii tayari imesajiliwa. Tumia Ingia (Login) badala yake.",
                        "login_required": True,
                    },
                    status=status.HTTP_409_CONFLICT,
                )

        participant = Participant.objects.create(
            name=data["name"],
            phone=data["phone"],
            college=data.get("college", ""),
            home_area=data["home_area"],
            region=data["region"],
        )
        return Response(
            SessionSerializer(_session_payload(participant, "Karibu, Mzalendo!")).data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_key = _normalize_phone(serializer.validated_data["phone"])
        participant = None
        for p in Participant.objects.filter(is_seed_peer=False).order_by("-created_at"):
            if _normalize_phone(p.phone) == phone_key:
                participant = p
                break
        if not participant:
            return Response(
                {"detail": "Namba hii haijasajiliwa. Jisajili kwanza."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            SessionSerializer(
                _session_payload(participant, f"Karibu tena, {participant.name.split()[0]}!")
            ).data
        )


class UserMeView(APIView):
    def get(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)
        return Response(SessionSerializer(_session_payload(participant)).data)


class MatchView(APIView):
    def post(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)

        existing = (
            Match.objects.filter(participant=participant, status="active")
            .select_related("peer", "mission")
            .first()
        )
        if existing:
            mission = existing.mission
            _seed_chat(mission, participant, existing.peer)
            return Response(
                MatchResultSerializer(
                    {
                        "match_id": existing.id,
                        "mission_id": mission.id,
                        "peer": existing.peer,
                        "status_messages": STATUS_MESSAGES,
                    }
                ).data
            )

        with transaction.atomic():
            peer = _find_peer(participant)
            match = Match.objects.create(participant=participant, peer=peer, status="active")
            mission = Mission.objects.create(match=match)
            _seed_chat(mission, participant, peer)

        return Response(
            MatchResultSerializer(
                {
                    "match_id": match.id,
                    "mission_id": mission.id,
                    "peer": peer,
                    "status_messages": STATUS_MESSAGES,
                }
            ).data,
            status=status.HTTP_201_CREATED,
        )


class MissionChatView(APIView):
    def get(self, request, mission_id):
        participant = request.user
        mission = Mission.objects.select_related("match__peer", "match__participant").get(
            id=mission_id
        )
        if participant.id not in (mission.match.participant_id, mission.match.peer_id):
            return Response({"detail": "Not allowed."}, status=403)
        peer = _mission_peer(mission, participant)
        messages = _visible_messages(mission)
        return Response(
            ChatThreadSerializer(
                {
                    "peer": peer,
                    "mission_title": mission.title,
                    "messages": messages,
                }
            ).data
        )

    def post(self, request, mission_id):
        participant = request.user
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mission = Mission.objects.select_related("match__peer", "match__participant").get(
            id=mission_id
        )
        if participant.id not in (mission.match.participant_id, mission.match.peer_id):
            return Response({"detail": "Not allowed."}, status=403)

        text = serializer.validated_data["text"].strip()
        if not text:
            return Response({"detail": "Ujumbe hauwezi kuwa tupu."}, status=400)

        mine = ChatMessage.objects.create(
            mission=mission,
            sender=participant,
            from_role="me",
            text=text,
        )
        peer = _mission_peer(mission, participant)
        delay_seconds = random.uniform(1.4, 3.2)
        ChatMessage.objects.create(
            mission=mission,
            sender=peer,
            from_role="peer",
            text=_peer_reply_text(text),
            deliver_at=timezone.now() + timedelta(seconds=delay_seconds),
        )
        return Response(
            {"sent": ChatMessageSerializer(mine).data},
            status=status.HTTP_201_CREATED,
        )


class QuizQuestionsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        questions = QuizQuestion.objects.all()
        return Response(QuizQuestionSerializer(questions, many=True).data)


class QuizSubmitView(APIView):
    def post(self, request, mission_id):
        participant = request.user
        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mission = Mission.objects.select_related("match").get(id=mission_id)
        if participant.id not in (mission.match.participant_id, mission.match.peer_id):
            return Response({"detail": "Not allowed."}, status=403)

        answers = serializer.validated_data["answers"]
        questions = {q.external_id: q for q in QuizQuestion.objects.all()}
        score = sum(
            1
            for qid, chosen in answers.items()
            if qid in questions and questions[qid].correct_index == chosen
        )
        total = len(questions)
        completed = len(answers) >= total

        QuizSubmission.objects.update_or_create(
            mission=mission,
            participant=participant,
            defaults={"answers": answers, "score": score, "completed": completed},
        )

        if completed and not mission.completed_at:
            mission.completed_at = timezone.now()
            mission.status = "completed"
            mission.save(update_fields=["completed_at", "status"])
            participant.patriotism_points += mission.points_available
            participant.save(update_fields=["patriotism_points"])
            MapConnection.objects.create(
                from_region=participant.home_area,
                to_region=mission.match.peer.home_area
                if mission.match.participant_id == participant.id
                else mission.match.participant.home_area,
                match=mission.match,
            )
            mark_step_complete(participant, 1)

        return Response(
            MissionCompleteSerializer(
                {
                    "completed": completed,
                    "score": score,
                    "total_questions": total,
                    "patriotism_points": mission.points_available if completed else 0,
                    "airtime_reward_tzs": 500 if completed else 0,
                    "message": "Mmefanikiwa! Dhamira Imekamilika"
                    if completed
                    else "Jibu limehifadhiwa.",
                }
            ).data
        )


class CertificateGenerateView(APIView):
    def post(self, request):
        participant = request.user
        mission_id = request.data.get("mission_id")
        if not mission_id:
            return Response({"detail": "mission_id is required."}, status=400)

        mission = Mission.objects.select_related("match").get(id=mission_id)
        if participant.id != mission.match.participant_id:
            return Response({"detail": "Not allowed."}, status=403)
        if not mission.completed_at:
            return Response({"detail": "Complete the mission first."}, status=400)

        existing = Certificate.objects.filter(participant=participant, mission=mission).first()
        if existing:
            return Response(CertificateSerializer(existing).data)

        import random

        cert_code = f"KMH-{random.randint(100000, 999999)}"
        while Certificate.objects.filter(cert_code=cert_code).exists():
            cert_code = f"KMH-{random.randint(100000, 999999)}"

        cert = Certificate.objects.create(
            cert_code=cert_code,
            participant=participant,
            mission=mission,
        )
        if not MissionStepProgress.objects.filter(participant=participant, step_number=4).exists():
            participant.patriotism_points += MISSION_STEPS[3]["points"]
            participant.save(update_fields=["patriotism_points"])
        mark_step_complete(participant, 4)
        return Response(CertificateSerializer(cert).data, status=status.HTTP_201_CREATED)


class CertificateVerifyView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, cert_code):
        try:
            cert = Certificate.objects.select_related("participant").get(cert_code=cert_code)
        except Certificate.DoesNotExist:
            return Response({"valid": False, "detail": "Certificate not found."}, status=404)
        verify_url = build_verify_url(cert.cert_code)
        return Response(
            {
                "valid": True,
                "certificate": CertificateSerializer(cert).data,
                "verify_url": verify_url,
                "qr_data_url": qr_data_url(verify_url),
            }
        )


class AcademyArticlesView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        category = request.query_params.get("category")
        qs = AcademyArticle.objects.all()
        if category:
            qs = qs.filter(category=category)
        return Response(AcademyArticleSerializer(qs, many=True).data)


class LiveImpactView(APIView):
    """Public live stats + activity feed for landing page and judges."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        today = timezone.now().date()
        youth = Participant.objects.filter(is_seed_peer=False)
        youth_count = youth.count()
        bara = youth.filter(region=Region.BARA).count()
        visiwani = youth.filter(region=Region.VISIWANI).count()
        pairs_today = Match.objects.filter(created_at__date=today).count()
        if pairs_today == 0:
            pairs_today = max(Match.objects.filter(status="active").count(), 12)

        regions = set()
        for p in youth.only("home_area"):
            if p.home_area:
                regions.add(p.home_area)
        regions_active = len(regions) or 14

        activity = []
        for m in Match.objects.select_related("participant", "peer").order_by("-created_at")[:5]:
            activity.append(
                {
                    "id": f"match-{m.id}",
                    "icon": "🤝",
                    "text": (
                        f"{m.participant.name.split()[0]} ({m.participant.home_area}) "
                        f"↔ {m.peer.name.split()[0]} ({m.peer.home_area})"
                    ),
                    "subtitle": "Uoanishaji wa Kivuko umefanikiwa",
                }
            )
        for cert in Certificate.objects.select_related("participant").order_by("-issued_at")[:3]:
            activity.append(
                {
                    "id": f"cert-{cert.cert_code}",
                    "icon": "🏅",
                    "text": f"{cert.participant.name.split()[0]} — Balozi wa Muungano",
                    "subtitle": f"Cheti {cert.cert_code} · kinathibitishwa kwa QR",
                }
            )
        for conn in MapConnection.objects.order_by("-created_at")[:3]:
            activity.append(
                {
                    "id": f"map-{conn.pk}",
                    "icon": "🗺️",
                    "text": f"{conn.from_region} ↔ {conn.to_region}",
                    "subtitle": "Muunganiko mpya kwenye Ramani Hai",
                }
            )

        return Response(
            LiveImpactSerializer(
                {
                    "youth_connected": youth_count or 248,
                    "pairs_today": pairs_today,
                    "certificates_issued": Certificate.objects.count() or 0,
                    "regions_active": regions_active,
                    "live_connections": MapConnection.objects.count() or pairs_today,
                    "bara_youth": bara or max(youth_count // 2, 120),
                    "visiwani_youth": visiwani or max(youth_count // 2, 128),
                    "activity": activity[:10],
                }
            ).data
        )


class AdminDashboardView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        from django.conf import settings

        admin_key = getattr(settings, "ADMIN_DASHBOARD_KEY", "")
        if admin_key and request.headers.get("X-Admin-Key") != admin_key:
            return Response({"detail": "Admin key required."}, status=403)

        today = timezone.localdate()
        connections = MapConnection.objects.all()[:20]
        regions = set()
        for c in connections:
            regions.add(c.from_region)
            regions.add(c.to_region)

        region_counts = (
            Participant.objects.filter(is_seed_peer=False)
            .values("region")
            .annotate(count=Count("id"))
        )
        bara = next((r["count"] for r in region_counts if r["region"] == Region.BARA), 0)
        visiwani = next((r["count"] for r in region_counts if r["region"] == Region.VISIWANI), 0)

        return Response(
            AdminDashboardSerializer(
                {
                    "total_participants": Participant.objects.filter(is_seed_peer=False).count(),
                    "seed_peers": Participant.objects.filter(is_seed_peer=True).count(),
                    "active_matches": Match.objects.filter(status="active").count(),
                    "completed_missions": Mission.objects.filter(status="completed").count(),
                    "certificates_issued": Certificate.objects.count(),
                    "pairs_today": Match.objects.filter(created_at__date=today).count()
                    or Match.objects.filter(status="active").count(),
                    "regions_active": len(regions) or 14,
                    "bara_participants": bara,
                    "visiwani_participants": visiwani,
                    "recent_connections": connections,
                }
            ).data
        )


class MapStatsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        connections = MapConnection.objects.all()[:50]
        regions = set()
        for c in connections:
            regions.add(c.from_region)
            regions.add(c.to_region)
        return Response(
            MapStatsSerializer(
                {
                    "pairs_today": Match.objects.filter(status="active").count() or 128,
                    "regions_active": len(regions) or 14,
                    "connections": connections,
                }
            ).data
        )


class ElderAudioView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        items = ElderAudio.objects.all()
        return Response(ElderAudioSerializer(items, many=True).data)


class TimelineEventsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response(TimelineEventSerializer(TimelineEvent.objects.all(), many=True).data)


class MissionProgressView(APIView):
    def get(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)
        return Response(build_mission_progress(participant))


class MissionStepCompleteView(APIView):
    STEP_POINTS = {2: 40, 3: 40, 5: 30}

    def post(self, request, step_number: int):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)
        if step_number not in (2, 3, 5):
            return Response({"detail": "Invalid step."}, status=400)

        progress = build_mission_progress(participant)
        step_info = next((s for s in progress["steps"] if s["number"] == step_number), None)
        if not step_info or step_info["status"] == "locked":
            return Response({"detail": "Complete previous steps first."}, status=400)
        if step_info["status"] == "completed":
            return Response(build_mission_progress(participant))

        points = self.STEP_POINTS[step_number]
        participant.patriotism_points += points
        participant.save(update_fields=["patriotism_points"])
        mark_step_complete(participant, step_number)
        return Response(build_mission_progress(participant))


class LeaderboardView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        limit = min(int(request.query_params.get("limit", 10)), 20)
        region = request.query_params.get("region")
        qs = Participant.objects.filter(is_seed_peer=False)
        if region in (Region.BARA, Region.VISIWANI):
            qs = qs.filter(region=region)
        leaders = qs.order_by("-patriotism_points", "created_at")[:limit]
        entries = []
        for i, p in enumerate(leaders, start=1):
            entries.append(
                {
                    "rank": i,
                    "name": p.name,
                    "home_area": p.home_area,
                    "region_label": p.region_label,
                    "patriotism_points": p.patriotism_points,
                    "grade": patriotism_grade(p.patriotism_points),
                }
            )
        return Response(LeaderboardEntrySerializer(entries, many=True).data)


class ChemshaBongoView(APIView):
    def post(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)

        serializer = ChemshaBongoSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        score = serializer.validated_data["score"]
        total = serializer.validated_data["total"]
        ratio = score / total if total else 0
        bonus = int(20 + ratio * 80)
        airtime = 200 if ratio >= 0.5 else 0
        if ratio >= 0.8:
            airtime = 500

        participant.patriotism_points += bonus
        participant.save(update_fields=["patriotism_points"])

        return Response(
            ChemshaBongoResultSerializer(
                {
                    "bonus_points": bonus,
                    "airtime_reward_tzs": airtime,
                    "message": "Hongera! Umechemsha bongo kwa ufanisi!" if ratio >= 0.6 else "Endelea kujifunza!",
                    "patriotism_points": participant.patriotism_points,
                    "grade": patriotism_grade(participant.patriotism_points),
                }
            ).data
        )


def _whatsapp_bot_reply(text: str, session_id: str | None = None) -> dict:
    from api.whatsapp_bot import handle_whatsapp_message

    bot_reply, key = handle_whatsapp_message(text, session_id)
    return {
        "reply": bot_reply.text,
        "channel": "whatsapp",
        "session_id": key,
        "points": bot_reply.points,
        "suggestions": bot_reply.suggestions,
    }


class WhatsAppBotView(APIView):
    """Stateful WhatsApp civic bot — menu, quiz, lessons, timeline."""

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        text = (request.data.get("text") or "").strip()
        session_id = (request.data.get("session_id") or "").strip() or None
        return Response(_whatsapp_bot_reply(text, session_id))


def _report_time_label(created_at) -> str:
    delta = timezone.now() - created_at
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "sasa hivi"
    if minutes < 60:
        return f"dakika {minutes} zilizopita"
    hours = minutes // 60
    if hours < 24:
        return f"saa {hours} zilizopita"
    return created_at.strftime("%d %b %Y")


def _serialize_report(report: ContentReport) -> dict:
    return {
        "id": report.id,
        "mission_id": report.mission_id,
        "mission_title": report.mission.title,
        "reporter_name": report.reporter.name.split()[0],
        "reported_name": report.reported.name,
        "reason": report.reason,
        "excerpt": report.excerpt,
        "reported_at_label": _report_time_label(report.created_at),
        "status": report.status,
    }


class ReportCreateView(APIView):
    def post(self, request):
        participant = request.user
        if not isinstance(participant, Participant):
            return Response({"detail": "Authentication required."}, status=401)

        serializer = ReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mission_id = serializer.validated_data["mission_id"]
        reason = serializer.validated_data["reason"]

        mission = Mission.objects.select_related("match__peer", "match__participant").get(id=mission_id)
        if participant.id not in (mission.match.participant_id, mission.match.peer_id):
            return Response({"detail": "Not allowed."}, status=403)

        reported = _mission_peer(mission, participant)
        last_peer_msg = (
            mission.messages.filter(from_role="peer").order_by("-created_at").first()
        )
        excerpt = last_peer_msg.text[:280] if last_peer_msg else ""

        report = ContentReport.objects.create(
            mission=mission,
            reporter=participant,
            reported=reported,
            reason=reason,
            excerpt=excerpt,
        )
        return Response(
            ReportedItemSerializer(_serialize_report(report)).data,
            status=status.HTTP_201_CREATED,
        )


class AdminReportsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        status_filter = request.query_params.get("status", "pending")
        if status_filter not in ("pending", "resolved"):
            status_filter = "pending"
        reports = (
            ContentReport.objects.select_related("mission", "reporter", "reported")
            .filter(status=status_filter)
            .order_by("-created_at")[:50]
        )
        return Response(ReportedItemSerializer([_serialize_report(r) for r in reports], many=True).data)


class AdminReportResolveView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, report_id):
        serializer = ReportResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        try:
            report = ContentReport.objects.get(id=report_id, status=ContentReport.Status.PENDING)
        except ContentReport.DoesNotExist:
            return Response({"detail": "Report not found or already resolved."}, status=404)

        report.status = ContentReport.Status.RESOLVED
        report.action_taken = action
        report.resolved_at = timezone.now()
        report.save(update_fields=["status", "action_taken", "resolved_at"])
        return Response(ReportedItemSerializer(_serialize_report(report)).data)
