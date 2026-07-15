"""
Deterministic identity for acquisition-to-assimilation handoffs.
"""

from __future__ import annotations

import hashlib


def build_assimilation_handoff_id(
    *,
    mission_id: str,
    candidate_id: str,
) -> str:
    """Build a stable handoff ID for one mission candidate."""

    normalized_mission = mission_id.strip()
    normalized_candidate = candidate_id.strip()

    if not normalized_mission:
        raise ValueError(
            "mission_id must not be empty"
        )

    if not normalized_candidate:
        raise ValueError(
            "candidate_id must not be empty"
        )

    payload = (
        f"{normalized_mission}\n{normalized_candidate}"
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


__all__ = [
    "build_assimilation_handoff_id",
]
