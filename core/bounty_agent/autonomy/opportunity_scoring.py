
"""R9.16C.3: deterministic offline opportunity scoring.

Ranks synthetic investigation opportunities without executing
tools, validating vulnerabilities, or authorizing submissions.
"""

from __future__ import annotations

import hashlib
import json


class ScoringError(ValueError):
    pass


def _integer(value, name, minimum=0, maximum=5):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ScoringError(f"Invalid {name}")
    return value


def score_opportunities(
    *,
    opportunities,
    authorized_target,
    available_capabilities,
    budget,
):
    """Rank synthetic opportunities under explicit constraints."""

    if (
        not isinstance(authorized_target, str)
        or not authorized_target.endswith(".example")
    ):
        raise ScoringError("Synthetic target required")

    _integer(budget, "budget", 1, 10)

    if not isinstance(opportunities, list):
        raise ScoringError("Opportunities must be a list")

    if not isinstance(available_capabilities, (list, tuple, set)):
        raise ScoringError("Invalid capability inventory")

    if not all(
        isinstance(item, str) and item
        for item in available_capabilities
    ):
        raise ScoringError("Invalid capability name")

    capabilities = set(available_capabilities)
    ranked = []

    for item in opportunities:
        if not isinstance(item, dict):
            raise ScoringError("Invalid opportunity")

        if item.get("target") != authorized_target:
            raise ScoringError("Opportunity outside approved target")

        if item.get("simulation_only") is not True:
            raise ScoringError("Non-synthetic evidence rejected")

        if item.get("validated_vulnerability") is not False:
            raise ScoringError("Vulnerability assertion rejected")

        evidence = item.get("evidence")
        if not isinstance(evidence, dict):
            raise ScoringError("Missing evidence")

        if (
            evidence.get("source") != "mock_adapter"
            or evidence.get("target") != authorized_target
        ):
            raise ScoringError("Untrusted evidence provenance")

        quality = _integer(
            item.get("evidence_quality"),
            "evidence_quality",
        )
        value = _integer(
            item.get("investigation_value"),
            "investigation_value",
        )
        effort = _integer(
            item.get("estimated_effort"),
            "estimated_effort",
            1,
            5,
        )

        capability = item.get("required_capability")
        if not isinstance(capability, str) or not capability:
            raise ScoringError("Missing required capability")

        evidence_digest = hashlib.sha256(
            json.dumps(
                evidence,
                sort_keys=True,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()

        # Investigation utility, NOT vulnerability probability.
        score = (
            quality * 4
            + value * 3
            - effort * 2
        )

        capability_available = capability in capabilities
        within_budget = effort <= budget

        blockers = []
        if not capability_available:
            blockers.append("capability_unavailable")
        if not within_budget:
            blockers.append("insufficient_budget")

        ranked.append({
            "target": authorized_target,
            "required_capability": capability,
            "evidence_sha256": evidence_digest,
            "priority_score": score,
            "estimated_effort": effort,
            "eligible": not blockers,
            "blockers": blockers,
            "vulnerability_confidence": 0,
            "validated_vulnerability": False,
            "recommended_action": (
                "request_human_review"
                if not blockers
                else "blocked"
            ),
            "execution_allowed": False,
            "approval_state": "not_approved",
        })

    ranked.sort(
        key=lambda item: (
            not item["eligible"],
            -item["priority_score"],
            item["estimated_effort"],
            item["required_capability"],
            item["evidence_sha256"],
        )
    )

    eligible = [item for item in ranked if item["eligible"]]

    return {
        "schema": "jarvis.bounty.opportunity_scoring.r916c3",
        "mode": "offline_scoring",
        "target": authorized_target,
        "budget": budget,
        "ranked_opportunities": ranked,
        "recommended": eligible[0] if eligible else None,
        "automatic_execution_allowed": False,
        "vulnerability_validation_allowed": False,
        "report_submission_allowed": False,
    }
