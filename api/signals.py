from django.db.models.signals import post_migrate

from api.models import AcademyArticle, ElderAudio, MapConnection, Participant, QuizQuestion, Region


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
                    external_id="a0",
                    name="Mwalimu Julius K. Nyerere",
                    area="Taifa",
                    duration_label="Sekunde 10 · Umoja na Muungano",
                ),
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

    if not AcademyArticle.objects.exists():
        AcademyArticle.objects.bulk_create(
            [
                AcademyArticle(
                    external_id="army-1",
                    category="army",
                    title="Ukumbi wa Jeshi: Tangu Tanganyika Rifles hadi JWTZ",
                    summary="Kufuatia uasi wa kikosi cha Tanganyika Rifles mnamo Januari 1964, Jeshi la Ulinzi la Wananchi wa Tanzania (JWTZ) liliundwa rasmi tarehe 1 Septemba 1964.",
                    body=(
                        "Kufuatia uasi wa kikosi cha Tanganyika Rifles mnamo Januari 1964, "
                        "Baba wa Taifa Mwalimu Julius Nyerere alichukua uamuzi wa kimkakati wa kulivunja jeshi la kikoloni. "
                        "Tarehe 1 Septemba 1964, Jeshi la Ulinzi la Wananchi wa Tanzania (JWTZ) liliundwa rasmi likiwa na "
                        "misingi mipya ya uzalendo, uaminifu, na utii kwa umma.\n\n"
                        "1964: Muungano uliunganisha vikosi vya Tanganyika na kile cha Zanzibar People's Liberation Army "
                        "kuwa jeshi moja imara.\n"
                        "1978–1979 (Vita vya Kagera): JWTZ ilionyesha mfano wa juu wa uzalendo kwa kumlinda na kumng'oa "
                        "mvamizi na kukomboa ardhi ya Tanzania."
                    ),
                    badge_label="Tukio la Kila Desemba / Septemba",
                    sort_order=1,
                ),
                AcademyArticle(
                    external_id="union-1",
                    category="union",
                    title="Nyaraka za Ndani za Hati ya Muungano",
                    summary="Muungano wa 26 Aprili 1964 uliunda Jamhuri ya Muungano wa Tanzania — taifa moja lenye historia, utamaduni, na hatima moja.",
                    body=(
                        "Tarehe 26 Aprili 1964, Rais wa Tanganyika Mwalimu Julius K. Nyerere na Rais wa Zanzibar "
                        "Sheikh Abeid Amani Karume walisaini makubaliano ya kuunda Jamhuri ya Muungano wa Tanzania.\n\n"
                        "Muungano huu uliunganisha Bara na Visiwani kwa utaratibu wa kisiasa, kiuchumi, na kijamii "
                        "uliowawezesha Watanzania kusafiri, kufanya biashara, na kujifunza kama taifa moja.\n\n"
                        "Leo, Kivuko la Muungano Hub linakumbuka kwamba umoja huu si tu kumbukumbu ya vitabu — "
                        "ni uzoefu wa kijana mmoja Bara na kijana mmoja Visiwani wakijenga daraja la kidijitali."
                    ),
                    badge_label="Nyaraka za 1964",
                    sort_order=2,
                ),
                AcademyArticle(
                    external_id="patriot-1",
                    category="patriot",
                    title="Misingi ya Uzalendo: Nembo, Wimbo, na Viapo",
                    summary="Uzalendo ni kujitoa kwa taifa — kulinda utu, utamaduni, na mustakabali wa Tanzania kwa vitendo, si maneno tu.",
                    body=(
                        "Uzalendo (patriotism) ni msingi wa taifa imara. Inajumuisha:\n\n"
                        "• Kuheshimu nembo na bendera ya Tanzania\n"
                        "• Kujua na kuimba Wimbo wa Taifa kwa fahari\n"
                        "• Kulinda amani na umoja wa kitaifa\n"
                        "• Kuchangia maendeleo ya jamii na nchi\n\n"
                        "Kupitia Kivuko la Muungano Hub, vijana wanapata pointi za Uzalendo kwa kukamilisha dhamira, "
                        "kujibu maswali ya historia, na kuungana na wenzao kutoka upande wa pili wa Muungano."
                    ),
                    badge_label="Nishani ya Uzalendo: Gredi A",
                    sort_order=3,
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
