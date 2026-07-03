"""Airtime / M-Pesa reward ledger with optional Africa's Talking disbursement."""

from __future__ import annotations

import secrets

from django.conf import settings
from django.utils import timezone

from api.models import Participant, RewardDisbursement


def grant_reward(
    participant: Participant,
    amount_tzs: int,
    reward_type: str,
    *,
    source: str = "",
    mission_id=None,
) -> RewardDisbursement:
    reward = RewardDisbursement.objects.create(
        participant=participant,
        amount_tzs=amount_tzs,
        reward_type=reward_type,
        status=RewardDisbursement.Status.PENDING,
        source=source,
        mission_id=mission_id,
    )
    if getattr(settings, "AUTO_DISBURSE_REWARDS", False):
        attempt_disburse(reward)
    return reward


def attempt_disburse(reward: RewardDisbursement) -> RewardDisbursement:
    """Try real or sandbox telco disbursement for a pending reward."""
    from api.telco import disburse_airtime

    if reward.status not in (
        RewardDisbursement.Status.PENDING,
        RewardDisbursement.Status.PROCESSING,
    ):
        return reward

    reward.status = RewardDisbursement.Status.PROCESSING
    reward.save(update_fields=["status"])

    if reward.reward_type == RewardDisbursement.RewardType.AIRTIME:
        result = disburse_airtime(reward.participant.phone, reward.amount_tzs)
        status = result.get("status", "failed")
        if status in ("sent", "sandbox"):
            reward.status = RewardDisbursement.Status.SENT
            reward.reference = result.get("reference") or f"KMH-{secrets.token_hex(4).upper()}"
            reward.sent_at = timezone.now()
        else:
            reward.status = RewardDisbursement.Status.FAILED
        reward.save(update_fields=["status", "reference", "sent_at"])
    return reward
