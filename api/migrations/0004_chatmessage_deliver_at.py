from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0003_timelineevent_missionstepprogress"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="deliver_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
