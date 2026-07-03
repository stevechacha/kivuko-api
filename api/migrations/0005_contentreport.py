from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0004_chatmessage_deliver_at"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentReport",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "reason",
                    models.CharField(
                        choices=[
                            ("abusive_language", "Abusive language"),
                            ("contact_request", "Contact request"),
                            ("inappropriate_content", "Inappropriate content"),
                            ("other", "Other"),
                        ],
                        max_length=32,
                    ),
                ),
                ("excerpt", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pending"), ("resolved", "Resolved")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("action_taken", models.CharField(blank=True, max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "mission",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="api.mission"),
                ),
                (
                    "reported",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports_received", to="api.participant"),
                ),
                (
                    "reporter",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports_filed", to="api.participant"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
