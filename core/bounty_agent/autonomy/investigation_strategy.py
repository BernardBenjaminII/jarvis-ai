
"""R9.16C: deterministic, non-executing investigation strategy."""

from __future__ import annotations

import hashlib
import json


class StrategyError(ValueError):
    pass


def build_strategy(*, artifact):
    """Rank synthetic evidence without asserting vulnerabilities."""
    if not isinstance(artifact, dict):
        raise StrategyError("Invalid mission artifact")

    if artifact.get("simulation_only") is not True:
        raise StrategyError("Only offline simulations supported")

    plan = artifact.get("recon_plan")
    if not isinstance(plan, dict):
        raise StrategyError("Missing reconnaissance plan")

    if (
        plan.get("execution_started") is not False
        or plan.get("automatic_execution_allowed") is not False
        or plan.get("authorization_id")
        != artifact.get("authorization_id")
    ):
        raise StrategyError("Invalid planning boundary")

    target = plan.get("target")
    if (
        not isinstance(target, str)
        or not target.endswith(".example")
        or not target
    ):
        raise StrategyError("Invalid synthetic target")

    if not isinstance(plan.get("tasks"), list):
        raise StrategyError("Invalid planned tasks")

    findings = artifact.get("findings")
    if not isinstance(findings, list):
        raise StrategyError("Invalid findings")

    opportunities = []

    for finding in findings:
        if not isinstance(finding, dict):
            raise StrategyError("Invalid finding")

        if finding.get("target") != target:
            raise StrategyError("Finding target mismatch")

        if finding.get("validated_vulnerability") is not False:
            raise StrategyError("Unexpected vulnerability assertion")

        evidence = finding.get("evidence")
        if not isinstance(evidence, dict):
            raise StrategyError("Missing evidence")

        if (
            evidence.get("source") != "mock_adapter"
            or evidence.get("target") != target
        ):
            raise StrategyError("Untrusted simulation evidence")

        evidence_digest = hashlib.sha256(
            json.dumps(
                evidence,
                sort_keys=True,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest()

        opportunities.append({
            "target": target,
            "classification": "synthetic_recon_observation",
            "evidence_sha256": evidence_digest,
            "evidence_quality": "synthetic_only",
            "priority_score": 0,
            "validated_vulnerability": False,
            "recommended_action": "human_review",
            "rationale": (
                "Mock observation only; no independently "
                "verified vulnerability evidence."
            ),
            "execution_allowed": False,
            "approval_state": "not_approved",
        })

    opportunities.sort(
        key=lambda item: (
            -item["priority_score"],
            item["target"],
            item["evidence_sha256"],
        )
    )

    return {
        "schema": "jarvis.bounty.investigation_strategy.r916c",
        "mode": "offline_strategy",
        "target": target,
        "authorization_id": artifact["authorization_id"],
        "opportunities": opportunities,
        "recommended_next_action": (
            "human_review" if opportunities else "await_evidence"
        ),
        "automatic_execution_allowed": False,
        "vulnerability_validation_allowed": False,
        "report_submission_allowed": False,
    }
