from django.core.management.base import BaseCommand

from api.quiz_sync import sync_quiz_questions


class Command(BaseCommand):
    help = "Upsert patriotism quiz questions from the canonical quiz bank."

    def handle(self, *args, **options):
        count = sync_quiz_questions()
        self.stdout.write(self.style.SUCCESS(f"Synced {count} quiz questions."))
