from django.core.management.base import BaseCommand

from api.models import ContentReport
from api.signals import _seed_demo_elders_radio


class Command(BaseCommand):
    help = "Seed demo elder radio nominees and mark demo moderation flags for pitch."

    def handle(self, *args, **options):
        _seed_demo_elders_radio()
        updated = ContentReport.objects.filter(
            reason=ContentReport.Reason.CONTACT,
            auto_flagged=False,
        ).update(auto_flagged=True)
        self.stdout.write(self.style.SUCCESS(f"Pitch demo seed complete (auto_flagged updated: {updated})."))
