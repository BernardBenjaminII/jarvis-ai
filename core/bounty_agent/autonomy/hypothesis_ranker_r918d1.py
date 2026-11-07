"""R9.18D.1: deterministic offline investigation reasoning.

Advisory only. No network, execution, payload generation,
authorization, or automatic vulnerability validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.bounty_agent.autonomy.experiment_planner_r918c2 import (
    EXPERIMENTS,
)
from core.bounty_agent.autonomy.hypothesis_engine_r918 import (
    HYPOTHESES,
)

SYNTAX_REPEAT = "syntax_repetition"
CAPABILITIES = frozenset(EXPERIMENTS) | {SYNTAX_REPEAT}

IDENTITIES = {
    **{name: exp.identity for name, exp in EXPERIMENTS.items()},
    SYNTAX_REPEAT: "repeat_syntax_apple_quote",
}

# Scores are ordinal heuristics, not probabilities.
PRIORITY = {
    "baseline_http": 100,
    "sql_syntax_diagnostic": 90,
    SYNTAX_REPEAT: 85,
    "boolean_comparison": 45,
    "reproducibility_check": 35,
}


class RankingError(ValueError):
    pass


@dataclass(frozen=True)
class RankedHypothesis:
    identifier: str
    score: int
    supporting_evidence: tuple[str, ...]
    contradicting_evidence: tuple[str, ...]


@dataclass(frozen=True)
class RankedExperiment:
    capability: str
    identity: str
    score: int
    rationale: str


@dataclass(frozen=True)
class RankingDecision:
    hypotheses: tuple[RankedHypothesis, ...]
    experiments: tuple[RankedExperiment, ...]
    evidence_gaps: tuple[str, ...]
    next_capability: str | None
    rationale: str
    execution_allowed: bool = False
    validated_vulnerability: bool = False
    human_review_required: bool = True


def rank(
    *,
    observations: list[dict[str, Any]],
    allowed_capabilities: frozenset[str],
    remaining_budget: int,
) -> RankingDecision:
    if type(remaining_budget) is not int or remaining_budget < 0:
        raise RankingError("Invalid budget")

    if (
        not isinstance(allowed_capabilities, frozenset)
        or not allowed_capabilities.issubset(CAPABILITIES)
    ):
        raise RankingError("Invalid capability set")

    if not isinstance(observations, list):
        raise RankingError("Invalid observations")

    seen = set()
    completed = {}
    failed = False

    for index, item in enumerate(observations):
        if not isinstance(item, dict):
            raise RankingError("Invalid observation")

        capability = item.get("capability")
        state = item.get("state")

        if capability not in CAPABILITIES:
            raise RankingError("Unknown capability")

        if capability in seen:
            raise RankingError("Duplicate capability")

        if state not in {"attempted", "completed", "failed"}:
            raise RankingError("Invalid state")

        if failed:
            raise RankingError("Observation after failure")

        if state == "attempted":
            raise RankingError("Unresolved attempt")

        if index == 0 and capability != "baseline_http":
            raise RankingError("Baseline must be first")

        seen.add(capability)

        if state == "completed":
            completed[capability] = item
        else:
            failed = True

    baseline = completed.get("baseline_http")
    syntax = completed.get("sql_syntax_diagnostic")
    repeat = completed.get(SYNTAX_REPEAT)
    variation = completed.get("boolean_comparison")
    baseline_repeat = completed.get("reproducibility_check")

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
        and type(syntax.get("http_status")) is int
        and syntax["http_status"] >= 500
        and not syntax.get("sqlite_error")
    )

    reproduced = bool(
        sql_signal
        and repeat
        and repeat.get("http_status") == 500
        and repeat.get("sqlite_error")
        and syntax.get("query_sha256")
        and syntax.get("query_sha256") == repeat.get("query_sha256")
    )

    if repeat and not sql_signal:
        raise RankingError("Repetition without original SQL signal")

    if repeat and (
        type(repeat.get("reproduces_syntax_error")) is not bool
        or repeat["reproduces_syntax_error"] != reproduced
    ):
        raise RankingError("Contradictory reproduction claim")

    gaps = []

    if not baseline_valid:
        gaps.append("valid_baseline_missing")

    if sql_signal and not repeat:
        gaps.append("syntax_condition_reproduction_missing")

    if variation is not None:
        gaps.append("true_false_differential_not_tested")

    if baseline_repeat is not None and sql_signal:
        gaps.append("baseline_repetition_is_not_syntax_reproduction")

    if sql_signal:
        gaps.append("exploitability_not_established")

    scores = {
        "sql_parser_interaction": (
            80 if reproduced else 60 if sql_signal else 0
        ),
        "generic_server_error": 40 if generic_error else 0,
        "transient_observation": (
            30 if sql_signal and not repeat
            else 10 if sql_signal and not reproduced
            else 0
        ),
    }

    supporting = {
        "sql_parser_interaction": (
            ("sqlite_error_observed", "syntax_error_reproduced")
            if reproduced
            else ("sqlite_error_observed",) if sql_signal else ()
        ),
        "generic_server_error": (
            ("server_error_without_sqlite_marker",)
            if generic_error else ()
        ),
        "transient_observation": (
            ("syntax_condition_not_reproduced",)
            if sql_signal and not reproduced else ()
        ),
    }

    contradicting = {
        "sql_parser_interaction": (),
        "generic_server_error": (
            ("sqlite_error_marker_present",) if sql_signal else ()
        ),
        "transient_observation": (
            ("syntax_error_reproduced",) if reproduced else ()
        ),
    }

    hypotheses = tuple(sorted(
        (
            RankedHypothesis(
                identifier=name,
                score=scores[name],
                supporting_evidence=supporting[name],
                contradicting_evidence=contradicting[name],
            )
            for name in HYPOTHESES
        ),
        key=lambda item: (-item.score, item.identifier),
    ))

    candidates = []

    if not failed and remaining_budget > 0:
        if not baseline_valid:
            choices = (
                ["baseline_http"]
                if "baseline_http" not in seen else []
            )
        elif syntax is None:
            choices = (
                ["sql_syntax_diagnostic"]
                if "sql_syntax_diagnostic" not in seen else []
            )
        elif sql_signal:
            choices = [
                name for name in (
                    SYNTAX_REPEAT,
                    "boolean_comparison",
                    "reproducibility_check",
                )
                if name not in seen
            ]
        else:
            choices = []

        for name in choices:
            if name not in allowed_capabilities:
                continue

            rationale = {
                "baseline_http": "Establish a valid control",
                "sql_syntax_diagnostic": "Check syntax-sensitive behavior",
                SYNTAX_REPEAT: "Reproduce the original SQL diagnostic",
                "boolean_comparison": "Compare benign input variation",
                "reproducibility_check": "Check baseline stability",
            }[name]

            candidates.append(RankedExperiment(
                capability=name,
                identity=IDENTITIES[name],
                score=PRIORITY[name],
                rationale=rationale,
            ))

    experiments = tuple(sorted(
        candidates,
        key=lambda item: (-item.score, item.capability),
    ))

    next_capability = (
        experiments[0].capability if experiments else None
    )

    if failed:
        reason = "Prior experiment failed; human review required"
    elif remaining_budget == 0:
        reason = "Request budget exhausted"
    elif next_capability:
        reason = experiments[0].rationale
    else:
        reason = "No useful permitted experiment available"

    return RankingDecision(
        hypotheses=hypotheses,
        experiments=experiments,
        evidence_gaps=tuple(gaps),
        next_capability=next_capability,
        rationale=reason,
    )
