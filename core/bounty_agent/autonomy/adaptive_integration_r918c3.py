"""R9.18C.3: bounded local-lab adaptive integration.

Uses the existing fixed-target executor. No arbitrary URLs,
commands, payloads, or external targets are accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Callable

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CAPABILITIES,
    CATALOG,
    LocalMission,
    execute_capability,
    validate_mission,
)
from core.bounty_agent.autonomy.execution_boundary_r918d3 import execute_verified
from core.bounty_agent.autonomy.experiment_planner_r918c2 import (
    EXPERIMENTS,
    select_next,
)


SYNTAX_REPEAT = "syntax_repetition"
MAX_EXPERIMENTS = 5


class IntegrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class IntegratedResult:
    observations: tuple[dict, ...]
    stop_reason: str
    request_count: int
    validated_vulnerability: bool = False
    human_review_required: bool = True
    submission_authorized: bool = False


def run_integrated(
    *,
    mission: LocalMission,
    runner: Callable[[str], dict] = execute_capability,
) -> IntegratedResult:
    """Execute approved experiments against the fixed local lab."""

    validate_mission(mission)

    if mission.max_requests > MAX_EXPERIMENTS:
        raise IntegrationError("Experiment budget exceeded")

    observations = []
    attempted = set()
    stop_reason = "request_budget_exhausted"

    for _ in range(mission.max_requests):
        completed = {
            item["capability"]: item
            for item in observations
            if item["state"] == "completed"
        }

        syntax = completed.get("sql_syntax_diagnostic")
        repeated = completed.get(SYNTAX_REPEAT)

        syntax_signal = bool(
            syntax
            and syntax.get("http_status") == 500
            and syntax.get("sqlite_error")
        )

        # The new experiment repeats the actual syntax condition,
        # not the normal baseline.
        if (
            syntax_signal
            and SYNTAX_REPEAT not in attempted
        ):
            capability = SYNTAX_REPEAT
            rationale = "Reproduce the syntax-sensitive condition"
        else:
            legacy_history = [
                item for item in observations
                if item["capability"] in CAPABILITIES
            ]

            decision = select_next(
                observations=legacy_history,
                allowed_capabilities=frozenset(
                    CAPABILITIES - attempted
                ),
                remaining_budget=(
                    mission.max_requests - len(observations)
                ),
            )

            if decision.action != "propose_test":
                stop_reason = decision.rationale
                break

            capability = decision.capability
            rationale = decision.rationale

        if capability in attempted:
            stop_reason = "experiment_already_attempted"
            break

        attempted.add(capability)

        identity = (
            "repeat_syntax_apple_quote"
            if capability == SYNTAX_REPEAT
            else EXPERIMENTS[capability].identity
        )

        entry = {
            "capability": capability,
            "experiment_identity": identity,
            "rationale": rationale,
            "state": "attempted",
        }
        observations.append(entry)

        # Execute through the shared verified boundary.
        # The current entry has already been recorded as attempted;
        # pass only preceding observations to duplicate detection.
        verified = execute_verified(
            capability=capability,
            runner=runner,
            observations=observations[:-1],
            rationale=rationale,
        )

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

    else:
        stop_reason = "request_budget_exhausted"

    return IntegratedResult(
        observations=tuple(observations),
        stop_reason=stop_reason,
        request_count=len(observations),
    )
