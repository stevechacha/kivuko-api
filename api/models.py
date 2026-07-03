import secrets
import uuid

from django.db import models


class Region(models.TextChoices):
    BARA = "bara", "Bara (Mainland)"
    VISIWANI = "visiwani", "Visiwani (Zanzibar)"


class Participant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=30)
    college = models.CharField(max_length=200, blank=True)
    home_area = models.CharField(max_length=120)
    region = models.CharField(max_length=20, choices=Region.choices)
    session_token = models.CharField(max_length=64, unique=True, blank=True)
    is_seed_peer = models.BooleanField(default=False)
    patriotism_points = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.session_token:
            self.session_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    @property
    def region_label(self) -> str:
        return "Zanzibar" if self.region == Region.VISIWANI else "Mainland"

    @property
    def initials(self) -> str:
        parts = self.name.split()
        return "".join(p[0].upper() for p in parts[:2]) or "??"


class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="matches_as_participant",
    )
    peer = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="matches_as_peer",
    )
    status = models.CharField(max_length=20, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Mission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match = models.OneToOneField(Match, on_delete=models.CASCADE, related_name="mission")
    title = models.CharField(max_length=200, default="Jaribio la Historia ya Muungano")
    status = models.CharField(max_length=20, default="active")
    points_available = models.PositiveIntegerField(default=50)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        Participant,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_messages",
    )
    from_role = models.CharField(max_length=10)  # me | peer | system
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    deliver_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    @property
    def is_visible(self) -> bool:
        from django.utils import timezone

        if self.deliver_at is None:
            return True
        return self.deliver_at <= timezone.now()


class QuizQuestion(models.Model):
    external_id = models.CharField(max_length=20, unique=True)
    question = models.TextField()
    options = models.JSONField()
    correct_index = models.PositiveSmallIntegerField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]


class QuizSubmission(models.Model):
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="quiz_submissions")
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE)
    answers = models.JSONField()
    score = models.PositiveSmallIntegerField(default=0)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("mission", "participant")]


class Certificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cert_code = models.CharField(max_length=20, unique=True)
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="certificates")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="certificates")
    issued_at = models.DateTimeField(auto_now_add=True)

    @property
    def verify_url(self) -> str:
        from api.utils import build_verify_url

        return build_verify_url(self.cert_code)


class MapConnection(models.Model):
    from_region = models.CharField(max_length=80)
    to_region = models.CharField(max_length=80)
    match = models.ForeignKey(
        Match,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="map_connections",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ElderAudio(models.Model):
    external_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    area = models.CharField(max_length=80)
    duration_label = models.CharField(max_length=120)
    audio_url = models.URLField(blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]


class AcademyCategory(models.TextChoices):
    ARMY = "army", "Historia ya JWTZ"
    UNION = "union", "Makumbusho ya Muungano"
    PATRIOT = "patriot", "Misingi ya Uzalendo"


class AcademyArticle(models.Model):
    external_id = models.CharField(max_length=30, unique=True)
    category = models.CharField(max_length=20, choices=AcademyCategory.choices)
    title = models.CharField(max_length=200)
    summary = models.TextField()
    body = models.TextField()
    badge_label = models.CharField(max_length=80, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]


class TimelineEvent(models.Model):
    external_id = models.CharField(max_length=30, unique=True)
    year = models.PositiveSmallIntegerField()
    month_label = models.CharField(max_length=40, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]


class MissionStepProgress(models.Model):
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="mission_steps",
    )
    step_number = models.PositiveSmallIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("participant", "step_number")]
        ordering = ["step_number"]


class ContentReport(models.Model):
    class Reason(models.TextChoices):
        ABUSIVE = "abusive_language", "Abusive language"
        CONTACT = "contact_request", "Contact request"
        INAPPROPRIATE = "inappropriate_content", "Inappropriate content"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RESOLVED = "resolved", "Resolved"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="reports_filed"
    )
    reported = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="reports_received"
    )
    reason = models.CharField(max_length=32, choices=Reason.choices)
    excerpt = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    action_taken = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class WhatsAppSession(models.Model):
    """Per-chat state for the omnichannel WhatsApp learning bot."""

    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    points = models.PositiveIntegerField(default=0)
    state = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"WA {self.session_key[:8]}… ({self.points} pts)"


class GalaNominee(models.Model):
    """Admin-curated Top 10 shortlist for the annual Uzalendo Gala."""

    participant = models.OneToOneField(
        Participant,
        on_delete=models.CASCADE,
        related_name="gala_nomination",
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-added_at"]


class OralStory(models.Model):
    """Culture-mission oral history submissions awaiting moderator review."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="oral_stories",
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    author_name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
