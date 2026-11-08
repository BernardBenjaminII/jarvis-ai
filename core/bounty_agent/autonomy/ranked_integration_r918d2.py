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
from core.bounty_agent.autonomy.investigation_planner_r918e1 import plan
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
    planner_mode: bool = False,
) -> IntegratedResult:
    """Run fixed-catalog experiments with optional ranked selection."""

    if type(ranked_mode) is not bool:
        raise RankedIntegrationError("Invalid ranked-mode flag")

    if type(planner_mode) is not bool:
        raise RankedIntegrationError("Invalid planner-mode flag")

    if planner_mode and not ranked_mode:
        raise RankedIntegrationError(
            "Planner mode requires ranked mode"
        )

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
            if planner_mode:
                decision = plan(
                    observations=observations,
                    allowed_capabilities=CAPABILITIES - attempted,
                    remaining_budget=(
                        mission.max_requests - len(observations)
                    ),
                )

                # Advisory output must never grant execution authority.
                if (
                    decision.execution_allowed is not False
                    or decision.validated_vulnerability is not False
                    or decision.human_review_required is not True
                    or decision.submission_authorized is not False
                ):
                    stop_reason = "invalid_planner_safety_flags"
                    break

                capability = decision.next_capability
                rationale = (
                    next(
                        (
                            candidate.rationale
                            for candidate in decision.candidates
                            if candidate.capability == capability
                        ),
                        None,
                    )
                    if capability is not None
                    else None
                )

                if capability is not None and rationale is None:
                    stop_reason = "invalid_planner_recommendation"
                    break
            else:
                decision = rank(
                    observations=observations,
                    allowed_capabilities=CAPABILITIES - attempted,
                    remaining_budget=(
                        mission.max_requests - len(observations)
                    ),
                )
                capability = decision.next_capability
                rationale = decision.rationale

        except RankingError:
            stop_reason = (
                "planner_evidence_failure"
                if planner_mode
                else "ranking_evidence_failure"
            )
            break
        except Exception:
            if not planner_mode:
                raise
            stop_reason = "planner_failure"
            break

        if capability is None:
            stop_reason = (
                decision.stop_reason
                if planner_mode
                else decision.rationale
            ) or "no_permitted_experiment"
            break

        if capability not in CAPABILITIES or capability in attempted:
            stop_reason = (
                "invalid_planner_recommendation"
                if planner_mode
                else "invalid_ranked_recommendation"
            )
            break

        attempted.add(capability)

        identity = IDENTITIES[capability]

        entry = {
            "capability": capability,
            "experiment_identity": identity,
            "rationale": rationale,
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
                rationale=rationale,
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
