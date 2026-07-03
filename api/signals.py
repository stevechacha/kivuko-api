from django.db.models.signals import post_migrate

from api.models import (
    AcademyArticle,
    ChatMessage,
    ContentReport,
    ElderAudio,
    Match,
    Mission,
    Participant,
    Region,
    TimelineEvent,
)
from api.quiz_sync import sync_quiz_questions

# Public-domain / Wikimedia audio clips for the elder archive.
ELDER_AUDIO_SEEDS = [
    {
        "external_id": "a0",
        "name": "Mwalimu Julius K. Nyerere",
        "area": "Taifa",
        "duration_label": "Wimbo wa Taifa · Tanzania",
        "audio_url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/National_Anthem_of_Tanzania.ogg",
        "sort_order": 0,
    },
    {
        "external_id": "a1",
        "name": "Bibi Fatuma",
        "area": "Pemba",
        "duration_label": "Sekunde 30 · 1964 ilivyokuwa",
        "audio_url": "https://upload.wikimedia.org/wikipedia/commons/1/1a/Tanzania_national_anthem_instrumental.ogg",
        "sort_order": 1,
    },
    {
        "external_id": "a2",
        "name": "Babu Elias",
        "area": "Kigoma",
        "duration_label": "Sekunde 30 · Siku ya Muungano",
        "audio_url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/National_Anthem_of_Tanzania.ogg",
        "sort_order": 2,
    },
]


def seed_demo_data(sender, **kwargs):
    if sender.name != "api":
        return

    sync_quiz_questions()

    for item in ELDER_AUDIO_SEEDS:
        ElderAudio.objects.update_or_create(
            external_id=item["external_id"],
            defaults=item,
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

    if not TimelineEvent.objects.exists():
        TimelineEvent.objects.bulk_create(
            [
                TimelineEvent(
                    external_id="t1",
                    year=1961,
                    month_label="Desemba",
                    title="Uhuru wa Tanganyika",
                    description="Tanganyika ilipata uhuru kutoka kwa utawala wa Uingereza chini ya uongozi wa Mwalimu Julius K. Nyerere.",
                    sort_order=1,
                ),
                TimelineEvent(
                    external_id="t2",
                    year=1964,
                    month_label="Januari",
                    title="Mapinduzi ya Zanzibar",
                    description="Mapinduzi yalibadilisha mwelekeo wa kisiasa Visiwani na kuweka msingi wa mazungumzo ya muungano.",
                    sort_order=2,
                ),
                TimelineEvent(
                    external_id="t3",
                    year=1964,
                    month_label="Aprili",
                    title="Muungano wa 26 Aprili",
                    description="Tanganyika na Zanzibar ziliunganishwa kuunda Jamhuri ya Muungano wa Tanzania.",
                    sort_order=3,
                ),
                TimelineEvent(
                    external_id="t4",
                    year=1964,
                    month_label="Septemba",
                    title="Kuzaliwa kwa JWTZ",
                    description="Jeshi la Ulinzi la Wananchi wa Tanzania liliundwa rasmi, likiunganisha vikosi vya Bara na Visiwani.",
                    sort_order=4,
                ),
                TimelineEvent(
                    external_id="t5",
                    year=1977,
                    month_label="",
                    title="Chama cha Mapinduzi",
                    description="CCM ilianzishwa kuendeleza umoja wa kisiasa na maendeleo ya taifa.",
                    sort_order=5,
                ),
                TimelineEvent(
                    external_id="t6",
                    year=2026,
                    month_label="Julai",
                    title="Kivuko la Muungano Hub",
                    description="Jukwaa la kidijitali linaunganisha vijana wa Bara na Visiwani kupitia dhamira za pamoja na elimu ya uzalendo.",
                    sort_order=6,
                ),
            ]
        )

    _seed_demo_peers()
    _seed_demo_moderation_queue()


def _seed_demo_peers() -> None:
    import secrets

    seeds = [
        {
            "name": "Khadija Mrisho",
            "phone": "0755 200 001",
            "college": "Chuo cha Zanzibar",
            "home_area": "Unguja",
            "region": Region.VISIWANI,
        },
        {
            "name": "Suleiman Faki",
            "phone": "0755 200 002",
            "college": "SUZA",
            "home_area": "Pemba",
            "region": Region.VISIWANI,
        },
        {
            "name": "Furaha Ndosi",
            "phone": "0755 200 003",
            "college": "UDSM",
            "home_area": "Mwanza",
            "region": Region.BARA,
        },
    ]
    for data in seeds:
        peer, created = Participant.objects.get_or_create(
            phone=data["phone"],
            defaults={**data, "is_seed_peer": True, "session_token": secrets.token_urlsafe(32)},
        )
        if not created and not peer.is_seed_peer:
            peer.is_seed_peer = True
            peer.save(update_fields=["is_seed_peer"])


def _seed_demo_moderation_queue() -> None:
    if ContentReport.objects.filter(status=ContentReport.Status.PENDING).exists():
        return

    bara = Participant.objects.filter(is_seed_peer=True, region=Region.BARA).first()
    visi = Participant.objects.filter(is_seed_peer=True, region=Region.VISIWANI).first()
    if not bara or not visi:
        return

    match = Match.objects.filter(participant=bara, peer=visi).first()
    if not match:
        match = Match.objects.create(participant=bara, peer=visi, status="active")
    mission, _ = Mission.objects.get_or_create(match=match)

    excerpt = "Naweza kukupa namba yangu ya simu kwenye WhatsApp?"
    if not mission.messages.filter(from_role="peer").exists():
        ChatMessage.objects.create(
            mission=mission,
            sender=visi,
            from_role="peer",
            text=excerpt,
        )

    ContentReport.objects.create(
        mission=mission,
        reporter=bara,
        reported=visi,
        reason=ContentReport.Reason.CONTACT,
        excerpt=excerpt,
    )
