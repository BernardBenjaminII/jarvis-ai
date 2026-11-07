"""R9.18A: offline, policy-constrained adaptive investigation planner."""

from dataclasses import dataclass
from typing import Any


class PlanningError(ValueError):
    pass


@dataclass(frozen=True)
class InvestigationDecision:
    action: str
    rationale: str
    capability: str | None
    execution_allowed: bool = False


CAPABILITIES = frozenset({
    "baseline_http",
    "sql_syntax_diagnostic",
    "boolean_comparison",
    "reproducibility_check",
})


def plan_next(
    *,
    observations: list[dict[str, Any]],
    allowed_capabilities: frozenset[str],
    remaining_budget: int,
) -> InvestigationDecision:
    """Choose a next action; never authorize its execution."""

    if not isinstance(remaining_budget, int) or isinstance(
        remaining_budget, bool
    ) or remaining_budget < 0:
        raise PlanningError("Invalid request budget")

    if not isinstance(observations, list) or not all(
        isinstance(item, dict) for item in observations
    ):
        raise PlanningError("Invalid observations")

    if not isinstance(allowed_capabilities, frozenset):
        raise PlanningError("Capabilities must be a frozenset")

    if not allowed_capabilities.issubset(CAPABILITIES):
        raise PlanningError("Unknown capability")

    if remaining_budget == 0:
        return InvestigationDecision(
            "stop", "Request budget exhausted", None
        )

    if not observations:
        candidate = "baseline_http"
        reason = "No baseline observation exists"
    else:
        latest = observations[-1]

        if latest.get("validated_local_lab") is True:
            candidate = "reproducibility_check"
            reason = "A candidate finding requires independent repetition"
        elif latest.get("sqlite_error"):
            candidate = "sql_syntax_diagnostic"
            reason = "SQL syntax failure requires diagnostic review"
        elif latest.get("behavioral_difference") is True:
            candidate = "reproducibility_check"
            reason = "Observed behavioral difference requires repetition"
        elif latest.get("baseline_complete") is True:
            candidate = "boolean_comparison"
            reason = "Baseline established; compare permitted conditions"
        else:
            candidate = "baseline_http"
            reason = "Baseline evidence is insufficient"

    if candidate not in allowed_capabilities:
        return InvestigationDecision(
            "stop",
            f"Required capability unavailable: {candidate}",
            None,
        )

    return InvestigationDecision(
        action="propose_test",
        rationale=reason,
        capability=candidate,
        execution_allowed=False,
    )
