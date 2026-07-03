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
    institution_code = serializers.CharField(max_length=40, required=False, allow_blank=True)
    accepted_terms = serializers.BooleanField()


class ReportCreateSerializer(serializers.Serializer):
    mission_id = serializers.UUIDField()
    reason = serializers.ChoiceField(
        choices=["abusive_language", "contact_request", "inappropriate_content", "other"]
    )


class ReportedItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    mission_id = serializers.UUIDField()
    mission_title = serializers.CharField()
    reporter_name = serializers.CharField()
    reported_name = serializers.CharField()
    reason = serializers.CharField()
    excerpt = serializers.CharField(allow_blank=True)
    reported_at_label = serializers.CharField()
    status = serializers.ChoiceField(choices=["pending", "resolved"])
    auto_flagged = serializers.BooleanField(required=False, default=False)


class ReportResolveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["dismiss", "warn", "suspend"])


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=30)


class SessionSerializer(serializers.Serializer):
    message = serializers.CharField(required=False)
    participant = ParticipantSerializer()
    active_mission_id = serializers.UUIDField(allow_null=True)
    active_match_id = serializers.UUIDField(allow_null=True)


class MatchResultSerializer(serializers.Serializer):
    match_id = serializers.UUIDField()
    mission_id = serializers.UUIDField()
    peer = ParticipantSerializer()
    status_messages = serializers.ListField(child=serializers.CharField())
    demo_twin = serializers.BooleanField(required=False, default=False)


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "from_role", "text", "created_at"]


class PeerSummarySerializer(serializers.ModelSerializer):
    region_label = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)

    class Meta:
        model = Participant
        fields = ["id", "name", "initials", "region", "region_label", "home_area"]


class ChatThreadSerializer(serializers.Serializer):
    peer = PeerSummarySerializer()
    mission_title = serializers.CharField()
    messages = ChatMessageSerializer(many=True)


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
    pending_reports = serializers.IntegerField()
    pending_stories = serializers.IntegerField()
    signups_today = serializers.IntegerField()
    gala_nominees = serializers.IntegerField()
    quiz_questions = serializers.IntegerField()
    platform_ready = serializers.BooleanField()
    pending_elders = serializers.IntegerField(required=False, default=0)
    pending_rewards = serializers.IntegerField(required=False, default=0)


class PlatformStatusSerializer(serializers.Serializer):
    api_online = serializers.BooleanField()
    youth_registered = serializers.IntegerField()
    seed_peers_ready = serializers.BooleanField()
    quiz_questions = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    demo_ready = serializers.BooleanField()
    message = serializers.CharField()


class GalaToggleSerializer(serializers.Serializer):
    nominated = serializers.BooleanField()


class LiveActivitySerializer(serializers.Serializer):
    id = serializers.CharField()
    icon = serializers.CharField()
    text = serializers.CharField()
    subtitle = serializers.CharField(required=False)


class LiveImpactSerializer(serializers.Serializer):
    youth_connected = serializers.IntegerField()
    pairs_today = serializers.IntegerField()
    certificates_issued = serializers.IntegerField()
    regions_active = serializers.IntegerField()
    live_connections = serializers.IntegerField()
    bara_youth = serializers.IntegerField()
    visiwani_youth = serializers.IntegerField()
    activity = LiveActivitySerializer(many=True)


class TimelineEventSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="external_id")

    class Meta:
        model = TimelineEvent
        fields = ["id", "year", "month_label", "title", "description"]


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    participant_id = serializers.UUIDField(required=False)
    name = serializers.CharField()
    home_area = serializers.CharField()
    region_label = serializers.CharField()
    patriotism_points = serializers.IntegerField()
    grade = serializers.DictField()
    gala_nominated = serializers.BooleanField(required=False, default=False)


class ChemshaBongoSubmitSerializer(serializers.Serializer):
    score = serializers.IntegerField(min_value=0)
    total = serializers.IntegerField(min_value=1)


class ChemshaBongoResultSerializer(serializers.Serializer):
    bonus_points = serializers.IntegerField()
    airtime_reward_tzs = serializers.IntegerField()
    message = serializers.CharField()


class OralStorySubmitSerializer(serializers.Serializer):
    responses = serializers.ListField(
        child=serializers.CharField(max_length=2000),
        min_length=1,
        max_length=5,
    )


class OralStorySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    author_name = serializers.CharField()
    body = serializers.CharField()
    status = serializers.CharField()
    created_at_label = serializers.CharField()


class OralStoryResolveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])
    patriotism_points = serializers.IntegerField(required=False)
    grade = serializers.DictField(required=False)


class InstitutionSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    home_area = serializers.CharField()
    region = serializers.CharField()


class ElderStorySubmitSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    body = serializers.CharField(max_length=5000)
    contributor_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    contributor_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    home_area = serializers.CharField(max_length=120, required=False, allow_blank=True)
    region = serializers.ChoiceField(choices=["bara", "visiwani"], required=False)
    audio_url = serializers.URLField(required=False, allow_blank=True)
    video_url = serializers.URLField(required=False, allow_blank=True)


class ElderStorySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    contributor_name = serializers.CharField()
    title = serializers.CharField()
    body = serializers.CharField()
    home_area = serializers.CharField()
    region = serializers.CharField()
    region_label = serializers.CharField()
    audio_url = serializers.CharField(allow_blank=True)
    video_url = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    radio_nominated = serializers.BooleanField()
    created_at_label = serializers.CharField()


class ElderStoryResolveSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["approve", "reject"])


class ElderRadioEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    story_id = serializers.UUIDField()
    contributor_name = serializers.CharField()
    title = serializers.CharField()
    home_area = serializers.CharField()
    region_label = serializers.CharField()
    audio_url = serializers.CharField(allow_blank=True)


class PartnerInstitutionSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    home_area = serializers.CharField()
    region = serializers.CharField()
    youth_count = serializers.IntegerField()


class PartnerDashboardSerializer(serializers.Serializer):
    youth_registered = serializers.IntegerField()
    pairs_today = serializers.IntegerField()
    certificates_issued = serializers.IntegerField()
    completed_missions = serializers.IntegerField()
    bara_youth = serializers.IntegerField()
    visiwani_youth = serializers.IntegerField()
    regions_active = serializers.IntegerField()
    institutions = PartnerInstitutionSerializer(many=True)
    pending_elder_stories = serializers.IntegerField()
    elder_radio_nominees = serializers.IntegerField()
    auto_flagged_pending = serializers.IntegerField()
    rewards_pending_tzs = serializers.IntegerField()
    recent_certificates = serializers.ListField(child=serializers.DictField())


class RadioYouthNomineeSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    name = serializers.CharField()
    home_area = serializers.CharField()
    region_label = serializers.CharField()
    patriotism_points = serializers.IntegerField()


class RadioPartnerSerializer(serializers.Serializer):
    station_name = serializers.CharField()
    segment_title = serializers.CharField()
    elder_nominees = ElderRadioEntrySerializer(many=True)
    youth_gala_nominees = RadioYouthNomineeSerializer(many=True)
    approved_elder_stories = serializers.IntegerField()
    broadcast_ready = serializers.BooleanField()


class GalaCeremonyYouthSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    name = serializers.CharField()
    home_area = serializers.CharField()
    region_label = serializers.CharField()
    patriotism_points = serializers.IntegerField()
    grade = serializers.DictField()
    gala_nominated = serializers.BooleanField()


class GalaCeremonySerializer(serializers.Serializer):
    event_title = serializers.CharField()
    live_mode = serializers.BooleanField()
    youth_finalists = GalaCeremonyYouthSerializer(many=True)
    elder_finalists = ElderRadioEntrySerializer(many=True)
    total_certificates = serializers.IntegerField()
    total_connections = serializers.IntegerField()
    average_patriotism_score = serializers.IntegerField()
    ceremony_message = serializers.CharField()


class RewardDisbursementSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    participant_name = serializers.CharField()
    participant_phone = serializers.CharField()
    amount_tzs = serializers.IntegerField()
    reward_type = serializers.CharField()
    status = serializers.CharField()
    source = serializers.CharField()
    reference = serializers.CharField(allow_blank=True)
    created_at_label = serializers.CharField()


class RewardDisburseSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["send", "processing", "fail"])


class UserRewardSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    amount_tzs = serializers.IntegerField()
    reward_type = serializers.CharField()
    status = serializers.CharField()
    source = serializers.CharField()
    created_at_label = serializers.CharField()


class RadioBroadcastScriptSerializer(serializers.Serializer):
    station_name = serializers.CharField()
    segment_title = serializers.CharField()
    broadcast_ready = serializers.BooleanField()
    script_sw = serializers.CharField()
    script_en = serializers.CharField()
    nominees = ElderRadioEntrySerializer(many=True)
