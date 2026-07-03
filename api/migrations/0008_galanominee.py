import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_oralstory"),
    ]

    operations = [
        migrations.CreateModel(
            name="GalaNominee",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("added_at", models.DateTimeField(auto_now_add=True)),
                (
                    "participant",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="gala_nomination",
                        to="api.participant",
                    ),
                ),
            ],
            options={
                "ordering": ["-added_at"],
            },
        ),
    ]
