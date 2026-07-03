import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_galanominee"),
    ]

    operations = [
        migrations.CreateModel(
            name="Institution",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=40, unique=True)),
                ("name", models.CharField(max_length=200)),
                ("home_area", models.CharField(max_length=120)),
                ("region", models.CharField(choices=[("bara", "Bara (Mainland)"), ("visiwani", "Visiwani (Zanzibar)")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="participant",
            name="institution",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="participants",
                to="api.institution",
            ),
        ),
        migrations.AddField(
            model_name="contentreport",
            name="auto_flagged",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="ElderStory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("contributor_name", models.CharField(max_length=200)),
                ("contributor_phone", models.CharField(blank=True, max_length=30)),
                ("home_area", models.CharField(max_length=120)),
                ("region", models.CharField(choices=[("bara", "Bara (Mainland)"), ("visiwani", "Visiwani (Zanzibar)")], max_length=20)),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField()),
                ("audio_url", models.URLField(blank=True)),
                ("video_url", models.URLField(blank=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")], default="pending", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="ElderRadioNominee",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "story",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="radio_nomination",
                        to="api.elderstory",
                    ),
                ),
            ],
            options={"ordering": ["-added_at"]},
        ),
        migrations.CreateModel(
            name="RewardDisbursement",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("amount_tzs", models.PositiveIntegerField()),
                ("reward_type", models.CharField(choices=[("airtime", "Airtime voucher"), ("mpesa", "M-Pesa")], default="airtime", max_length=16)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("sent", "Sent"), ("failed", "Failed")], default="pending", max_length=16)),
                ("source", models.CharField(blank=True, max_length=120)),
                ("reference", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "mission",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="rewards",
                        to="api.mission",
                    ),
                ),
                (
                    "participant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rewards",
                        to="api.participant",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
