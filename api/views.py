import random

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import (
    Certificate,
    ChatMessage,
    ElderAudio,
    MapConnection,
    Match,
    Mission,
    Participant,
    QuizQuestion,
    QuizSubmission,
    Region,
)
from api.serializers import (
    CertificateSerializer,
    ChatMessageSerializer,
    ElderAudioSerializer,
    MapStatsSerializer,
    MatchResultSerializer,
    MissionCompleteSerializer,
    ParticipantSerializer,
    QuizQuestionSerializer,
    QuizSubmitSerializer,
    RegisterSerializer,
    SendMessageSerializer,
)

STATUS_MESSAGES = [
    "Inatafuta wanachama Visiwani…",
    "Inalinganisha maslahi ya kihistoria…",
    "Inathibitisha muunganiko wa kivuko…",
]

PEER_REPLIES = [
    "Vizuri sana! 🙌",
    "Nakubaliana nawe.",
    "Hii ni sehemu yangu pendwa ya historia yetu!",
]


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
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        participant = Participant.objects.create(
            name=data["name"],
            phone=data["phone"],
            college=data.get("college", ""),
            home_area=data["home_area"],
            region=data["region"],
        )
        return Response(
            {
                "message": "Karibu, Mzalendo!",
                "participant": ParticipantSerializer(participant).data,
            },
            status=status.HTTP_201_CREATED,
        )


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
        messages = mission.messages.all()
        return Response(ChatMessageSerializer(messages, many=True).data)

    def post(self, request, mission_id):
        participant = request.user
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mission = Mission.objects.select_related("match").get(id=mission_id)
        if participant.id not in (mission.match.participant_id, mission.match.peer_id):
            return Response({"detail": "Not allowed."}, status=403)

        text = serializer.validated_data["text"]
        mine = ChatMessage.objects.create(
            mission=mission,
            sender=participant,
            from_role="me",
            text=text,
        )
        peer_reply = ChatMessage.objects.create(
            mission=mission,
            sender=mission.match.peer if mission.match.participant_id == participant.id else mission.match.participant,
            from_role="peer",
            text=random.choice(PEER_REPLIES),
        )
        return Response(
            {
                "sent": ChatMessageSerializer(mine).data,
                "reply": ChatMessageSerializer(peer_reply).data,
            },
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
        return Response(CertificateSerializer(cert).data, status=status.HTTP_201_CREATED)


class CertificateVerifyView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, cert_code):
        try:
            cert = Certificate.objects.select_related("participant").get(cert_code=cert_code)
        except Certificate.DoesNotExist:
            return Response({"valid": False, "detail": "Certificate not found."}, status=404)
        return Response(
            {
                "valid": True,
                "certificate": CertificateSerializer(cert).data,
            }
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
