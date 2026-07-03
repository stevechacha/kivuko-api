"""Sync quiz bank into the database."""

from api.models import QuizQuestion
from api.quiz_bank import QUIZ_BANK


def sync_quiz_questions() -> int:
    """Upsert all canonical questions so new deploys add/update jaribio content."""
    count = 0
    for item in QUIZ_BANK:
        QuizQuestion.objects.update_or_create(
            external_id=item["external_id"],
            defaults={
                "question": item["question"],
                "options": item["options"],
                "correct_index": item["correct_index"],
                "sort_order": item["sort_order"],
            },
        )
        count += 1
    return count
