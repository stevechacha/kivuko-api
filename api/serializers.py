from rest_framework import serializers

from api.models import (
    Certificate,
    ChatMessage,
    ElderAudio,
    MapConnection,
    Match,
    Mission,
    Participant,
    QuizQuestion,
    AcademyArticle,
    TimelineEvent,
)


class ParticipantSerializer(serializers.ModelSerializer):
    region_label = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    patriotism_grade = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = [
            "id",
            "name",
            "phone",
            "college",
            "home_area",
            "region",
            "region_label",
            "initials",
            "patriotism_points",
            "patriotism_grade",
            "session_token",
            "created_at",
        ]
        read_only_fields = fields

    def get_patriotism_grade(self, obj):
        from api.grades import patriotism_grade

        return patriotism_grade(obj.patriotism_points)


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=30)
    college = serializers.CharField(max_length=200, required=False, allow_blank=True)
    home_area = serializers.CharField(max_length=120)
    region = serializers.ChoiceField(choices=["bara", "visiwani"])


class MatchResultSerializer(serializers.Serializer):
    match_id = serializers.UUIDField()
    mission_id = serializers.UUIDField()
    peer = ParticipantSerializer()
    status_messages = serializers.ListField(child=serializers.CharField())


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "from_role", "text", "created_at"]


class SendMessageSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=2000)


class QuizQuestionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="external_id")

    class Meta:
        model = QuizQuestion
        fields = ["id", "question", "options", "correct_index"]


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.IntegerField(min_value=0))


class MissionCompleteSerializer(serializers.Serializer):
    completed = serializers.BooleanField()
    score = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    patriotism_points = serializers.IntegerField()
    airtime_reward_tzs = serializers.IntegerField()
    message = serializers.CharField()


class CertificateSerializer(serializers.ModelSerializer):
    verify_url = serializers.CharField(read_only=True)
    user_name = serializers.CharField(source="participant.name", read_only=True)
    issued_date = serializers.SerializerMethodField()
    qr_data_url = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ["cert_code", "user_name", "verify_url", "issued_date", "qr_data_url"]

    def get_issued_date(self, obj):
        return obj.issued_at.strftime("%d/%m/%Y")

    def get_qr_data_url(self, obj):
        from api.utils import build_verify_url, qr_data_url

        return qr_data_url(build_verify_url(obj.cert_code))


class MapConnectionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="pk")

    class Meta:
        model = MapConnection
        fields = ["id", "from_region", "to_region"]


class MapStatsSerializer(serializers.Serializer):
    pairs_today = serializers.IntegerField()
    regions_active = serializers.IntegerField()
    connections = MapConnectionSerializer(many=True)


class ElderAudioSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="external_id")

    class Meta:
        model = ElderAudio
        fields = ["id", "name", "area", "duration_label", "audio_url"]


class AcademyArticleSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="external_id")

    class Meta:
        model = AcademyArticle
        fields = ["id", "category", "title", "summary", "body", "badge_label"]


class AdminDashboardSerializer(serializers.Serializer):
    total_participants = serializers.IntegerField()
    seed_peers = serializers.IntegerField()
    active_matches = serializers.IntegerField()
    completed_missions = serializers.IntegerField()
    certificates_issued = serializers.IntegerField()
    pairs_today = serializers.IntegerField()
    regions_active = serializers.IntegerField()
    bara_participants = serializers.IntegerField()
    visiwani_participants = serializers.IntegerField()
    recent_connections = MapConnectionSerializer(many=True)


class TimelineEventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="external_id")

    class Meta:
        model = TimelineEvent
        fields = ["id", "year", "month_label", "title", "description"]


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    name = serializers.CharField()
    home_area = serializers.CharField()
    region_label = serializers.CharField()
    patriotism_points = serializers.IntegerField()
    grade = serializers.DictField()


class ChemshaBongoSubmitSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0)
    total = serializers.IntegerField(min_value=1)


class ChemshaBongoResultSerializer(serializers.Serializer):
    bonus_points = serializers.IntegerField()
    airtime_reward_tzs = serializers.IntegerField()
    message = serializers.CharField()
    patriotism_points = serializers.IntegerField()
    grade = serializers.DictField()
