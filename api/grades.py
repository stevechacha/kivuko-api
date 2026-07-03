"""Uzalendo grade and 5-step Joint Mission journey definitions."""

MISSION_STEPS = [
    {
        "number": 1,
        "title": "Historia ya Muungano",
        "subtitle": "Jaribio la pamoja na pacha wako kuhusu Muungano wa 1964",
        "icon": "📜",
        "points": 50,
    },
    {
        "number": 2,
        "title": "Ubadilishanaji wa Utamaduni",
        "subtitle": "Shiriki mila, chakula, na lugha kutoka Bara na Visiwani",
        "icon": "🎭",
        "points": 40,
    },
    {
        "number": 3,
        "title": "Maono ya Mustakabali",
        "subtitle": "Andika maono yako ya Tanzania ya kesho pamoja na pacha",
        "icon": "🔭",
        "points": 40,
    },
    {
        "number": 4,
        "title": "Cheti cha Balozi",
        "subtitle": "Pata cheti chenye QR kinachothibitishwa kwa CV yako",
        "icon": "🏅",
        "points": 100,
    },
    {
        "number": 5,
        "title": "Ramani Hai ya Muungano",
        "subtitle": "Ona jozi yako ikionyesha kwenye ramani ya taifa",
        "icon": "🗺️",
        "points": 30,
    },
]


def patriotism_grade(points: int) -> dict:
    if points >= 300:
        return {
            "code": "A",
            "label": "Balozi wa Muungano",
            "badge": "🏆",
            "next_threshold": None,
        }
    if points >= 150:
        return {
            "code": "B",
            "label": "Mwanajadi wa Uzalendo",
            "badge": "⭐",
            "next_threshold": 300,
        }
    if points >= 50:
        return {
            "code": "C",
            "label": "Mzalendo Anayechangia",
            "badge": "🌱",
            "next_threshold": 150,
        }
    return {
        "code": "D",
        "label": "Mwanzo wa Safari",
        "badge": "🚩",
        "next_threshold": 50,
    }
