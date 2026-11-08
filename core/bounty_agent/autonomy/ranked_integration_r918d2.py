"""R9.18D.2: opt-in ranked local-lab integration.

Legacy mode delegates unchanged to R9.18C.3.
Ranked mode uses D.1 recommendations, but never treats
a recommendation as execution authorization.
"""

from __future__ import annotations

import hashlib
from typing import Callable

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG,
    LocalMission,
    execute_capability,
    validate_mission,
)
from core.bounty_agent.autonomy.adaptive_integration_r918c3 import (
    IntegratedResult,
    MAX_EXPERIMENTS,
    SYNTAX_REPEAT,
    run_integrated,
)
from core.bounty_agent.autonomy.execution_boundary_r918d3 import BoundaryError, execute_verified
from core.bounty_agent.autonomy.hypothesis_ranker_r918d1 import (
    CAPABILITIES,
    IDENTITIES,
    RankingError,
    rank,
)


class RankedIntegrationError(RuntimeError):
    pass


def run_ranked(
    *,
    mission: LocalMission,
    runner: Callable[[str], dict] = execute_capability,
    ranked_mode: bool = False,
) -> IntegratedResult:
    """Run fixed-catalog experiments with optional ranked selection."""

    if type(ranked_mode) is not bool:
        raise RankedIntegrationError("Invalid ranked-mode flag")

    if not ranked_mode:
        return run_integrated(mission=mission, runner=runner)

    validate_mission(mission)

    if mission.max_requests > MAX_EXPERIMENTS:
        raise RankedIntegrationError("Experiment budget exceeded")

    observations = []
    attempted = set()
    stop_reason = "request_budget_exhausted"

    for _ in range(mission.max_requests):
        try:
            decision = rank(
                observations=observations,
                allowed_capabilities=CAPABILITIES - attempted,
                remaining_budget=(
                    mission.max_requests - len(observations)
                ),
            )
        except RankingError as exc:
            stop_reason = "ranking_evidence_failure"
            break

        capability = decision.next_capability

        if capability is None:
            stop_reason = decision.rationale
            break

        if capability not in CAPABILITIES or capability in attempted:
            stop_reason = "invalid_ranked_recommendation"
            break

        attempted.add(capability)

        identity = IDENTITIES[capability]

        entry = {
            "capability": capability,
            "experiment_identity": identity,
            "rationale": decision.rationale,
            "state": "attempted",
        }
        observations.append(entry)

        # Ranked selection is advisory. Execution and evidence
        # verification use the same boundary as legacy C.3.
        try:
            verified = execute_verified(
                capability=capability,
                runner=runner,
                observations=observations[:-1],
                rationale=decision.rationale,
            )
        except BoundaryError:
            entry["state"] = "failed"
            entry["failure_category"] = "evidence_integrity_failure"
            stop_reason = "execution_or_evidence_failure"
            break

        entry.clear()
        entry.update(verified)

        if entry["state"] == "failed":
            stop_reason = "execution_or_evidence_failure"
            break

        if capability == "baseline_http" and (
            entry.get("valid_product_response") is not True
        ):
            stop_reason = "invalid_baseline"
            break

    return IntegratedResult(
        observations=tuple(observations),
        stop_reason=stop_reason,
        request_count=len(observations),
    )
