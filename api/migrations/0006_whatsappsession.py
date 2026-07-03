# Generated manually for WhatsAppSession

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_contentreport"),
    ]

    operations = [
        migrations.CreateModel(
            name="WhatsAppSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_key", models.CharField(db_index=True, max_length=64, unique=True)),
                ("points", models.PositiveIntegerField(default=0)),
                ("state", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
    ]
