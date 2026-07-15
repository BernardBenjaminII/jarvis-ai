"""
Deterministic identity helpers for acquisition missions.
"""

from __future__ import annotations

import hashlib


def build_acquisition_mission_id(
    *,
    request_id: str,
    provider_id: str,
    campaign_id: str | None,
) -> str:
    """Build a stable mission ID from its logical identity."""

    normalized_request = request_id.strip()
    normalized_provider = provider_id.strip().lower()
    normalized_campaign = (
        campaign_id.strip()
        if campaign_id is not None
        else ""
    )

    if not normalized_request:
        raise ValueError(
            "request_id must not be empty"
        )

    if not normalized_provider:
        raise ValueError(
            "provider_id must not be empty"
        )

    payload = "\n".join(
        (
            normalized_request,
            normalized_provider,
            normalized_campaign,
        )
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


__all__ = [
    "build_acquisition_mission_id",
]
