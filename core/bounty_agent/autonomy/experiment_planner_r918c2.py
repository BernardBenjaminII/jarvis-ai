"""R9.18C.2: bounded, offline experiment selection.

This module proposes experiments. It never executes or authorizes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.bounty_agent.autonomy.hypothesis_engine_r918 import (
    CAPABILITIES,
    HypothesisError,
    assess,
)


@dataclass(frozen=True)
class Experiment:
    capability: str
    identity: str
    purpose: str
    repeats_identity: str | None = None


EXPERIMENTS = {
    "baseline_http": Experiment(
        "baseline_http",
        "baseline_apple",
        "Establish normal application behavior",
    ),
    "sql_syntax_diagnostic": Experiment(
        "sql_syntax_diagnostic",
        "syntax_apple_quote",
        "Observe handling of a syntax-sensitive input",
    ),
    "boolean_comparison": Experiment(
        "boolean_comparison",
        "variation_apple_percent",
        "Compare a benign input variation against baseline",
    ),
    "reproducibility_check": Experiment(
        "reproducibility_check",
        "repeat_baseline_apple",
        "Verify baseline stability",
        repeats_identity="baseline_apple",
    ),
}


@dataclass(frozen=True)
class ExperimentDecision:
    action: str
    capability: str | None
    experiment_identity: str | None
    rationale: str
    evidence_gaps: tuple[str, ...]
    classification: str
    execution_allowed: bool = False


class ExperimentPlanningError(ValueError):
    pass


def _completed(
    observations: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    completed = {}
    seen = set()

    for observation in observations:
        if not isinstance(observation, dict):
            raise ExperimentPlanningError("Invalid observation")

        capability = observation.get("capability")
        state = observation.get("state")

        if capability not in EXPERIMENTS:
            raise ExperimentPlanningError("Unknown capability")

        if state not in {"attempted", "completed", "failed"}:
            raise ExperimentPlanningError("Invalid state")

        if capability in seen:
            raise ExperimentPlanningError("Duplicate experiment")

        seen.add(capability)

        if state == "completed":
            completed[capability] = observation

    return completed


def select_next(
    *,
    observations: list[dict[str, Any]],
    allowed_capabilities: frozenset[str],
    remaining_budget: int,
) -> ExperimentDecision:
    """Select the next permitted experiment using observed evidence."""

    if not isinstance(observations, list):
        raise ExperimentPlanningError("Invalid observations")

    if (
        type(remaining_budget) is not int
        or remaining_budget < 0
    ):
        raise ExperimentPlanningError("Invalid budget")

    if (
        not isinstance(allowed_capabilities, frozenset)
        or not allowed_capabilities.issubset(CAPABILITIES)
    ):
        raise ExperimentPlanningError("Invalid capability set")

    completed = _completed(observations)
    attempted = {item["capability"] for item in observations}

    try:
        assessment = assess(
            observations=observations,
            allowed_capabilities=allowed_capabilities,
            remaining_budget=remaining_budget,
        )
    except HypothesisError as exc:
        raise ExperimentPlanningError(
            "Hypothesis assessment rejected observations"
        ) from exc

    baseline = completed.get("baseline_http")
    syntax = completed.get("sql_syntax_diagnostic")
    variation = completed.get("boolean_comparison")
    repeated_baseline = completed.get("reproducibility_check")

    baseline_valid = (
        baseline is not None
        and baseline.get("valid_product_response") is True
    )

    sql_signal = (
        syntax is not None
        and syntax.get("http_status") == 500
        and bool(syntax.get("sqlite_error"))
    )

    gaps = []

    if not baseline_valid:
        gaps.append("valid_baseline_missing")

    if sql_signal:
        # No existing R9.18B capability repeats the syntax probe.
        gaps.append("syntax_condition_reproduction_missing")

    if variation is not None:
        gaps.append("true_false_differential_not_tested")

    if repeated_baseline is not None and sql_signal:
        gaps.append(
            "baseline_repetition_does_not_reproduce_sql_error"
        )

    def stop(reason: str) -> ExperimentDecision:
        return ExperimentDecision(
            action="stop",
            capability=None,
            experiment_identity=None,
            rationale=reason,
            evidence_gaps=tuple(gaps),
            classification=assessment.classification,
        )

    if remaining_budget == 0:
        return stop("Request budget exhausted")

    if not baseline_valid:
        candidate = "baseline_http"
        reason = "Establish a valid baseline"
    elif syntax is None and "sql_syntax_diagnostic" not in attempted:
        candidate = "sql_syntax_diagnostic"
        reason = "Evaluate syntax-sensitive input handling"
    elif sql_signal and variation is None:
        candidate = "boolean_comparison"
        reason = (
            "Compare permitted input variation; "
            "this is not a true/false SQL differential"
        )
    elif (
        sql_signal
        and repeated_baseline is None
        and "reproducibility_check" not in attempted
    ):
        candidate = "reproducibility_check"
        reason = (
            "Verify baseline stability; this does not "
            "reproduce the syntax error"
        )
    else:
        return stop(
            "Available experiments exhausted or "
            "insufficient evidence for further testing"
        )

    if candidate in attempted:
        return stop("Required experiment already attempted")

    if candidate not in allowed_capabilities:
        return stop("Required experiment unavailable")

    experiment = EXPERIMENTS[candidate]

    return ExperimentDecision(
        action="propose_test",
        capability=candidate,
        experiment_identity=experiment.identity,
        rationale=reason,
        evidence_gaps=tuple(gaps),
        classification=assessment.classification,
    )
