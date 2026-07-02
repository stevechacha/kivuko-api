from django.contrib import admin

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
)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "home_area", "phone", "is_seed_peer", "created_at")
    list_filter = ("region", "is_seed_peer")
    search_fields = ("name", "phone", "home_area")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("id", "participant", "peer", "status", "created_at")


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("id", "match", "title", "status", "completed_at")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("mission", "from_role", "text", "created_at")


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("external_id", "question", "correct_index", "sort_order")


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ("mission", "participant", "score", "completed", "created_at")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("cert_code", "participant", "mission", "issued_at")


@admin.register(MapConnection)
class MapConnectionAdmin(admin.ModelAdmin):
    list_display = ("from_region", "to_region", "created_at")


@admin.register(ElderAudio)
class ElderAudioAdmin(admin.ModelAdmin):
    list_display = ("external_id", "name", "area", "duration_label")
