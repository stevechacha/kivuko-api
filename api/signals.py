from django.db.models.signals import post_migrate

from api.models import ElderAudio, MapConnection, Participant, QuizQuestion, Region


def seed_demo_data(sender, **kwargs):
    if sender.name != "api":
        return

    if not QuizQuestion.objects.exists():
        QuizQuestion.objects.bulk_create(
            [
                QuizQuestion(
                    external_id="q1",
                    question="Muungano wa Tanganyika na Zanzibar ulianzishwa tarehe gani?",
                    options=["26 Aprili 1964", "9 Desemba 1961", "12 Januari 1964"],
                    correct_index=0,
                    sort_order=1,
                ),
                QuizQuestion(
                    external_id="q2",
                    question="Muungano uliunda nchi gani?",
                    options=[
                        "Jamhuri ya Kenya",
                        "Jamhuri ya Muungano wa Tanzania",
                        "Shirikisho la Afrika Mashariki",
                    ],
                    correct_index=1,
                    sort_order=2,
                ),
                QuizQuestion(
                    external_id="q3",
                    question="Rais wa kwanza wa Zanzibar baada ya mapinduzi alikuwa nani?",
                    options=["Julius K. Nyerere", "Abeid Amani Karume", "Ali Hassan Mwinyi"],
                    correct_index=1,
                    sort_order=3,
                ),
            ]
        )

    if not ElderAudio.objects.exists():
        ElderAudio.objects.bulk_create(
            [
                ElderAudio(
                    external_id="a1",
                    name="Bibi Fatuma",
                    area="Pemba",
                    duration_label="Sekunde 30 · 1964 ilivyokuwa",
                ),
                ElderAudio(
                    external_id="a2",
                    name="Babu Elias",
                    area="Kigoma",
                    duration_label="Sekunde 30 · Siku ya Muungano",
                ),
            ]
        )

    if not MapConnection.objects.exists():
        MapConnection.objects.bulk_create(
            [
                MapConnection(from_region="Mwanza", to_region="Unguja"),
                MapConnection(from_region="Dodoma", to_region="Pemba"),
                MapConnection(from_region="Mbeya", to_region="Unguja"),
                MapConnection(from_region="Dar es Salaam", to_region="Pemba"),
            ]
        )

    if not Participant.objects.filter(is_seed_peer=True).exists():
        import secrets

        seeds = [
            Participant(
                name="Khadija Mrisho",
                phone="0755 200 001",
                college="Chuo cha Zanzibar",
                home_area="Unguja",
                region=Region.VISIWANI,
                is_seed_peer=True,
                session_token=secrets.token_urlsafe(32),
            ),
            Participant(
                name="Suleiman Faki",
                phone="0755 200 002",
                college="SUZA",
                home_area="Pemba",
                region=Region.VISIWANI,
                is_seed_peer=True,
                session_token=secrets.token_urlsafe(32),
            ),
            Participant(
                name="Furaha Ndosi",
                phone="0755 200 003",
                college="UDSM",
                home_area="Mwanza",
                region=Region.BARA,
                is_seed_peer=True,
                session_token=secrets.token_urlsafe(32),
            ),
        ]
        Participant.objects.bulk_create(seeds)
