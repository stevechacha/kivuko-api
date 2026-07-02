from django.urls import path

from api.views import (
    CertificateGenerateView,
    CertificateVerifyView,
    ElderAudioView,
    MapStatsView,
    MatchView,
    MissionChatView,
    QuizQuestionsView,
    QuizSubmitView,
    RegisterView,
)

urlpatterns = [
    path("users/register", RegisterView.as_view(), name="register"),
    path("matching/match", MatchView.as_view(), name="match"),
    path("missions/<uuid:mission_id>/chat", MissionChatView.as_view(), name="mission-chat"),
    path("quiz/questions", QuizQuestionsView.as_view(), name="quiz-questions"),
    path("missions/<uuid:mission_id>/quiz/submit", QuizSubmitView.as_view(), name="quiz-submit"),
    path("certificates/generate", CertificateGenerateView.as_view(), name="certificate-generate"),
    path("certificates/verify/<str:cert_code>", CertificateVerifyView.as_view(), name="certificate-verify"),
    path("map/stats", MapStatsView.as_view(), name="map-stats"),
    path("audio/archive", ElderAudioView.as_view(), name="audio-archive"),
]
