"""Airtime / M-Pesa reward ledger — sandbox disbursement tracking."""

from __future__ import annotations

from api.models import Participant, RewardDisbursement


def grant_reward(
    participant: Participant,
    amount_tzs: int,
    reward_type: str,
    *,
    source: str = "",
    mission_id=None,
) -> RewardDisbursement:
    return RewardDisbursement.objects.create(
        participant=participant,
        amount_tzs=amount_tzs,
        reward_type=reward_type,
        status=RewardDisbursement.Status.PENDING,
        source=source,
        mission_id=mission_id,
    )
