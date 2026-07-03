from django.urls import path

from api.views import (
    AcademyArticlesView,
    AdminDashboardView,
    CertificateGenerateView,
    CertificateVerifyView,
    ElderAudioView,
    MapStatsView,
    MatchView,
    MissionChatView,
    QuizQuestionsView,
    QuizSubmitView,
    RegisterView,
    UserMeView,
)

urlpatterns = [
    path("users/register", RegisterView.as_view(), name="register"),
    path("users/me", UserMeView.as_view(), name="user-me"),
    path("matching/match", MatchView.as_view(), name="match"),
    path("missions/<uuid:mission_id>/chat", MissionChatView.as_view(), name="mission-chat"),
    path("quiz/questions", QuizQuestionsView.as_view(), name="quiz-questions"),
    path("missions/<uuid:mission_id>/quiz/submit", QuizSubmitView.as_view(), name="quiz-submit"),
    path("certificates/generate", CertificateGenerateView.as_view(), name="certificate-generate"),
    path("certificates/verify/<str:cert_code>", CertificateVerifyView.as_view(), name="certificate-verify"),
    path("academy/articles", AcademyArticlesView.as_view(), name="academy-articles"),
    path("admin/dashboard", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("map/stats", MapStatsView.as_view(), name="map-stats"),
    path("audio/archive", ElderAudioView.as_view(), name="audio-archive"),
]
