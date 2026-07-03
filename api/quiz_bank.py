"""Canonical patriotism / union history quiz bank — synced to DB on every migrate."""

from __future__ import annotations

from typing import TypedDict


class QuizBankItem(TypedDict):
    external_id: str
    question: str
    options: list[str]
    correct_index: int
    sort_order: int


# Swahili-first civic quiz: 1961 uhuru → 2026 Kivuko Hub (updated for demo/judges).
QUIZ_BANK: list[QuizBankItem] = [
    {
        "external_id": "q1",
        "question": "Muungano wa Tanganyika na Zanzibar ulianzishwa tarehe gani?",
        "options": ["26 Aprili 1964", "9 Desemba 1961", "12 Januari 1964"],
        "correct_index": 0,
        "sort_order": 1,
    },
    {
        "external_id": "q2",
        "question": "Muungano uliunda nchi gani?",
        "options": [
            "Jamhuri ya Kenya",
            "Jamhuri ya Muungano wa Tanzania",
            "Shirikisho la Afrika Mashariki",
        ],
        "correct_index": 1,
        "sort_order": 2,
    },
    {
        "external_id": "q3",
        "question": "Rais wa kwanza wa Zanzibar baada ya Mapinduzi ya 1964 alikuwa nani?",
        "options": ["Julius K. Nyerere", "Abeid Amani Karume", "Ali Hassan Mwinyi"],
        "correct_index": 1,
        "sort_order": 3,
    },
    {
        "external_id": "q4",
        "question": "Mji mkuu rasmi wa Tanzania ni upi?",
        "options": ["Dar es Salaam", "Dodoma", "Zanzibar"],
        "correct_index": 1,
        "sort_order": 4,
    },
    {
        "external_id": "q5",
        "question": "Lugha rasmi ya Tanzania ni ipi?",
        "options": ["Kiingereza tu", "Kiswahili", "Kiarabu tu"],
        "correct_index": 1,
        "sort_order": 5,
    },
    {
        "external_id": "q6",
        "question": "Visiwa vikuu vya Zanzibar ni vipi?",
        "options": ["Unguja na Pemba", "Mafia na Pemba", "Lamu na Unguja"],
        "correct_index": 0,
        "sort_order": 6,
    },
    {
        "external_id": "q7",
        "question": "Tanganyika ilipata uhuru kutoka kwa ukoloni mwaka gani?",
        "options": ["1959", "1961", "1964"],
        "correct_index": 1,
        "sort_order": 7,
    },
    {
        "external_id": "q8",
        "question": "Mapinduzi ya Zanzibar yalitokea mwezi upi wa 1964?",
        "options": ["Januari", "Aprili", "Septemba"],
        "correct_index": 0,
        "sort_order": 8,
    },
    {
        "external_id": "q9",
        "question": "Jeshi la Ulinzi la Wananchi wa Tanzania (JWTZ) liliundwa rasmi mwaka gani?",
        "options": ["1961", "1964", "1977"],
        "correct_index": 1,
        "sort_order": 9,
    },
    {
        "external_id": "q10",
        "question": "Chama cha Mapinduzi (CCM) kiliundwa mwaka gani?",
        "options": ["1964", "1977", "1992"],
        "correct_index": 1,
        "sort_order": 10,
    },
    {
        "external_id": "q11",
        "question": "Baba wa Taifa aliyeongoza mchakato wa Muungano alijulikana kama nani?",
        "options": ["Abeid Amani Karume", "Julius K. Nyerere", "John Magufuli"],
        "correct_index": 1,
        "sort_order": 11,
    },
    {
        "external_id": "q12",
        "question": "Lengo kuu la Muungano wa Tanzania ni lipi?",
        "options": [
            "Kuunganisha Bara na Visiwani kuwa taifa moja",
            "Kuunda shirikisho la nchi za Afrika Mashariki",
            "Kubadilisha mji mkuu kuwa Dar es Salaam",
        ],
        "correct_index": 0,
        "sort_order": 12,
    },
    {
        "external_id": "q13",
        "question": "Vita vya Kagera (1978–1979) vilionyesha nini kuhusu JWTZ?",
        "options": [
            "Uzalendo na ulinzi wa ardhi ya taifa",
            "Kuondoka katika Umoja wa Mataifa",
            "Kuanzisha fedha mpya ya Afrika",
        ],
        "correct_index": 0,
        "sort_order": 13,
    },
    {
        "external_id": "q14",
        "question": "Dar es Salaam ilikuwa mji mkuu wa kihistoria kabla ya uhamisho wa serikali kwenda wapi?",
        "options": ["Arusha", "Dodoma", "Mwanza"],
        "correct_index": 1,
        "sort_order": 14,
    },
    {
        "external_id": "q15",
        "question": "Tanzania ina mikoa mingapi (kufikia muundo wa sasa wa utawala)?",
        "options": ["26", "31", "47"],
        "correct_index": 1,
        "sort_order": 15,
    },
    {
        "external_id": "q16",
        "question": "Rais wa sasa wa Jamhuri ya Muungano wa Tanzania (2026) ni nani?",
        "options": [
            "Samia Suluhu Hassan",
            "Jakaya Mrisho Kikwete",
            "John Pombe Magufuli",
        ],
        "correct_index": 0,
        "sort_order": 16,
    },
    {
        "external_id": "q17",
        "question": "Kivuko la Muungano Hub lilizinduliwa mwaka gani kama daraja la kidijitali kwa vijana?",
        "options": ["2019", "2024", "2026"],
        "correct_index": 2,
        "sort_order": 17,
    },
    {
        "external_id": "q18",
        "question": "Nembo ya Tanzania ina rangi gani kuu (kati ya hizi)?",
        "options": [
            "Nyekundu, dhahabu, na bluu",
            "Kijani, nyeupe, na njano tu",
            "Rangi moja tu — kijani",
        ],
        "correct_index": 0,
        "sort_order": 18,
    },
]
