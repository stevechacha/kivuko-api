from django.contrib import admin

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
    TimelineEvent,
    WhatsAppSession,
    OralStory,
    GalaNominee,
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


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    list_display = ("reported", "reporter", "reason", "status", "action_taken", "created_at")
    list_filter = ("status", "reason")


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


@admin.register(AcademyArticle)
class AcademyArticleAdmin(admin.ModelAdmin):
    list_display = ("external_id", "category", "title", "sort_order")
    list_filter = ("category",)


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    list_display = ("external_id", "year", "title", "sort_order")


@admin.register(MissionStepProgress)
class MissionStepProgressAdmin(admin.ModelAdmin):
    list_display = ("participant", "step_number", "completed_at")


@admin.register(GalaNominee)
class GalaNomineeAdmin(admin.ModelAdmin):
    list_display = ("participant", "added_at")


@admin.register(OralStory)
class OralStoryAdmin(admin.ModelAdmin):
    list_display = ("title", "author_name", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "author_name", "body")


@admin.register(WhatsAppSession)
class WhatsAppSessionAdmin(admin.ModelAdmin):
    list_display = ("session_key", "points", "updated_at", "created_at")
    search_fields = ("session_key",)
    readonly_fields = ("session_key", "state", "created_at", "updated_at")
