"""R9.18E.1: offline evidence-driven investigation planning.

Advisory only. No network, execution, authorization, or submission.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.bounty_agent.autonomy.hypothesis_ranker_r918d1 import (
    CAPABILITIES,
    rank,
)


# Deterministic heuristic values, not calibrated probabilities.
EVIDENCE_VALUE = {
    "baseline_http": 100,
    "sql_syntax_diagnostic": 90,
    "syntax_repetition": 85,
    "boolean_comparison": 65,
    "reproducibility_check": 50,
}

# Relative effort for each fixed-catalog experiment.
EXPERIMENT_COST = {
    capability: 1 for capability in CAPABILITIES
}


@dataclass(frozen=True)
class InvestigationCandidate:
    capability: str
    information_value: int
    relative_cost: int
    utility: int
    rationale: str


@dataclass(frozen=True)
class InvestigationPlan:
    candidates: tuple[InvestigationCandidate, ...]
    next_capability: str | None
    stop_reason: str | None
    evidence_gaps: tuple[str, ...]
    execution_allowed: bool = False
    validated_vulnerability: bool = False
    human_review_required: bool = True
    submission_authorized: bool = False


def plan(
    *,
    observations: list[dict],
    allowed_capabilities: frozenset[str],
    remaining_budget: int,
) -> InvestigationPlan:
    """Recommend one approved experiment or stop.

    D.1 owns evidence validation and experiment eligibility.
    E.1 only ranks eligible recommendations by heuristic utility.
    """

    decision = rank(
        observations=observations,
        allowed_capabilities=allowed_capabilities,
        remaining_budget=remaining_budget,
    )

    candidates = []

    for experiment in decision.experiments:
        capability = experiment.capability

        if capability not in EVIDENCE_VALUE:
            continue

        if capability not in allowed_capabilities:
            continue

        if capability in {
            item.get("capability") for item in observations
        }:
            continue

        value = EVIDENCE_VALUE[capability]
        cost = EXPERIMENT_COST[capability]

        candidates.append(
            InvestigationCandidate(
                capability=capability,
                information_value=value,
                relative_cost=cost,
                utility=value - (cost * 5),
                rationale=(
                    "Approved fixed-catalog experiment; "
                    "heuristic evidence value only"
                ),
            )
        )

    candidates.sort(
        key=lambda item: (
            -item.utility,
            item.capability,
        )
    )

    # The existing ranker controls whether investigation may continue.
    # Never override its stop decision.
    if decision.next_capability is None:
        return InvestigationPlan(
            candidates=tuple(candidates),
            next_capability=None,
            stop_reason=decision.rationale,
            evidence_gaps=tuple(decision.evidence_gaps),
        )

    # D.1's recommendation is the eligibility gate. E.1 must not
    # independently authorize a different experiment.
    selected = next(
        (
            item for item in candidates
            if item.capability == decision.next_capability
        ),
        None,
    )

    if selected is None:
        return InvestigationPlan(
            candidates=tuple(candidates),
            next_capability=None,
            stop_reason="No eligible ranked experiment",
            evidence_gaps=tuple(decision.evidence_gaps),
        )

    return InvestigationPlan(
        candidates=tuple(candidates),
        next_capability=selected.capability,
        stop_reason=None,
        evidence_gaps=tuple(decision.evidence_gaps),
    )
