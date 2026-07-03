from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0009_proposal_gap_features"),
    ]

    operations = [
        migrations.CreateModel(
            name="PeerRating",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("stars", models.PositiveSmallIntegerField()),
                ("comment", models.CharField(blank=True, max_length=280)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "mission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="peer_ratings",
                        to="api.mission",
                    ),
                ),
                (
                    "rater",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="peer_ratings_given",
                        to="api.participant",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="peerrating",
            constraint=models.UniqueConstraint(fields=("mission", "rater"), name="unique_peer_rating_per_mission"),
        ),
    ]
