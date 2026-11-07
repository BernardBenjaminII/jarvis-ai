"""R9.18C.1: offline, evidence-driven hypothesis assessment.

No network, shell, authorization, or execution capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


CAPABILITIES = frozenset({
    "baseline_http",
    "sql_syntax_diagnostic",
    "boolean_comparison",
    "reproducibility_check",
})

HYPOTHESES = (
    "sql_parser_interaction",
    "generic_server_error",
    "transient_observation",
)

CONFIDENCE = ("unsupported", "possible", "supported")


class HypothesisError(ValueError):
    pass


@dataclass(frozen=True)
class Hypothesis:
    identifier: str
    confidence: str
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]


@dataclass(frozen=True)
class Assessment:
    hypotheses: tuple[Hypothesis, ...]
    next_capability: str | None
    rationale: str
    classification: str
    human_review_required: bool = True
    validated_vulnerability: bool = False
    execution_allowed: bool = False


def assess(
    *,
    observations: list[dict[str, Any]],
    allowed_capabilities: frozenset[str],
    remaining_budget: int,
) -> Assessment:
    """Assess completed observations and propose a permitted next test."""

    if (
        type(remaining_budget) is not int
        or remaining_budget < 0
    ):
        raise HypothesisError("Invalid budget")

    if (
        not isinstance(allowed_capabilities, frozenset)
        or not allowed_capabilities.issubset(CAPABILITIES)
    ):
        raise HypothesisError("Invalid capability set")

    if not isinstance(observations, list) or not all(
        isinstance(item, dict) for item in observations
    ):
        raise HypothesisError("Invalid observations")

    completed: dict[str, Mapping[str, Any]] = {}

    for item in observations:
        capability = item.get("capability")

        if capability not in CAPABILITIES:
            raise HypothesisError("Unknown observed capability")

        if item.get("state") not in (
            "attempted", "completed", "failed"
        ):
            raise HypothesisError("Invalid observation state")

        if capability in completed or (
            capability in {
                previous.get("capability")
                for previous in observations[:observations.index(item)]
            }
        ):
            raise HypothesisError("Duplicate capability")

        if item["state"] == "completed":
            completed[capability] = item

    baseline = completed.get("baseline_http")
    syntax = completed.get("sql_syntax_diagnostic")
    comparison = completed.get("boolean_comparison")
    repetition = completed.get("reproducibility_check")

    baseline_valid = bool(
        baseline and baseline.get("valid_product_response") is True
    )

    sql_signal = bool(
        syntax
        and syntax.get("http_status") == 500
        and syntax.get("sqlite_error")
    )

    generic_error = bool(
        syntax
        and isinstance(syntax.get("http_status"), int)
        and syntax["http_status"] >= 500
        and not syntax.get("sqlite_error")
    )

    comparison_changed = bool(
        comparison
        and baseline_valid
        and comparison.get("valid_product_response") is True
        and comparison.get("product_ids")
        != baseline.get("product_ids")
    )

    repeat_stable = bool(
        repetition
        and baseline_valid
        and repetition.get("valid_product_response") is True
        and repetition.get("product_ids")
        == baseline.get("product_ids")
    )

    hypotheses = (
        Hypothesis(
            identifier="sql_parser_interaction",
            confidence="supported" if sql_signal else "unsupported",
            supporting_evidence=(
                ("sql_syntax_diagnostic:sqlite_error",)
                if sql_signal else ()
            ),
            contradicting_evidence=(),
        ),
        Hypothesis(
            identifier="generic_server_error",
            confidence="possible" if generic_error else "unsupported",
            supporting_evidence=(
                ("sql_syntax_diagnostic:http_5xx",)
                if generic_error else ()
            ),
            contradicting_evidence=(
                ("sql_syntax_diagnostic:sqlite_error",)
                if sql_signal else ()
            ),
        ),
        Hypothesis(
            identifier="transient_observation",
            confidence=(
                "possible" if sql_signal else "unsupported"
            ),
            supporting_evidence=(
                ("sql_syntax_diagnostic:not_independently_reproduced",)
                if sql_signal else ()
            ),
            contradicting_evidence=(),
        ),
    )

    next_capability = None
    rationale = "No further permitted experiment required"

    attempted = {
        item["capability"] for item in observations
    }

    if remaining_budget == 0:
        rationale = "Request budget exhausted"
    elif not baseline_valid:
        if "baseline_http" not in attempted:
            next_capability = "baseline_http"
            rationale = "Establish a valid control response"
        else:
            rationale = "Baseline unavailable or invalid"
    elif syntax is None and "sql_syntax_diagnostic" not in attempted:
        next_capability = "sql_syntax_diagnostic"
        rationale = "Distinguish normal behavior from syntax failure"
    elif sql_signal and comparison is None and (
        "boolean_comparison" not in attempted
    ):
        next_capability = "boolean_comparison"
        rationale = "Investigate the SQL error with a permitted input variation"
    elif (
        (sql_signal or comparison_changed)
        and repetition is None
        and "reproducibility_check" not in attempted
    ):
        next_capability = "reproducibility_check"
        rationale = "Check whether the baseline remains stable"
    elif generic_error:
        rationale = "Generic server error requires human review"
    else:
        rationale = "Available diagnostic evidence assessed"

    if next_capability not in allowed_capabilities:
        if next_capability is not None:
            rationale = "Recommended capability unavailable"
        next_capability = None

    classification = (
        "sql_diagnostic_signal"
        if sql_signal
        else "behavioral_difference_observed"
        if comparison_changed
        else "inconclusive"
    )

    return Assessment(
        hypotheses=hypotheses,
        next_capability=next_capability,
        rationale=rationale,
        classification=classification,
    )
