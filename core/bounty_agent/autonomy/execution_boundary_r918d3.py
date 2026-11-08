"""R9.18D.3: shared fixed-catalog experiment execution boundary."""

from __future__ import annotations

import hashlib
from typing import Callable

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    CATALOG,
)
from core.bounty_agent.autonomy.experiment_planner_r918c2 import (
    EXPERIMENTS,
)


SYNTAX_REPEAT = "syntax_repetition"


class BoundaryError(RuntimeError):
    """Executor output or experiment prerequisites are invalid."""


def execute_verified(
    *,
    capability: str,
    runner: Callable[[str], dict],
    observations: list[dict],
    rationale: str,
) -> dict:
    """Execute one approved catalog experiment and verify its evidence.

    The caller must validate mission authorization and request budget.
    This function never authorizes execution independently.
    """

    if capability == SYNTAX_REPEAT:
        execution_capability = "sql_syntax_diagnostic"
        identity = "repeat_syntax_apple_quote"
    elif capability in EXPERIMENTS:
        execution_capability = capability
        identity = EXPERIMENTS[capability].identity
    else:
        raise BoundaryError("Unapproved experiment")

    if execution_capability not in CATALOG:
        raise BoundaryError("Experiment outside approved catalog")

    if any(
        item.get("capability") == capability
        for item in observations
    ):
        raise BoundaryError("Experiment already attempted")

    original = None

    if capability == SYNTAX_REPEAT:
        original = next(
            (
                item for item in observations
                if item.get("capability") == "sql_syntax_diagnostic"
                and item.get("state") == "completed"
            ),
            None,
        )

        if (
            original is None
            or original.get("http_status") != 500
            or not original.get("sqlite_error")
        ):
            raise BoundaryError(
                "Syntax repetition prerequisite failed"
            )

    entry = {
        "capability": capability,
        "experiment_identity": identity,
        "rationale": rationale,
        "state": "attempted",
    }

    try:
        result = runner(execution_capability)

        if not isinstance(result, dict):
            raise BoundaryError("Invalid executor result")

        if result.get("capability") != execution_capability:
            raise BoundaryError("Executor capability mismatch")

        query_hash = result.get("query_sha256")
        canonical_query = CATALOG[execution_capability][1]
        expected_hash = hashlib.sha256(
            canonical_query.encode("utf-8")
        ).hexdigest()

        if (
            not isinstance(query_hash, str)
            or query_hash != expected_hash
        ):
            raise BoundaryError(
                "Executor query differs from approved catalog"
            )

        if capability == SYNTAX_REPEAT:
            if original.get("query_sha256") != query_hash:
                raise BoundaryError(
                    "Syntax repetition query mismatch"
                )

        entry.update(result)
        entry["capability"] = capability
        entry["experiment_identity"] = identity
        entry["rationale"] = rationale
        entry["state"] = "completed"

        if capability == SYNTAX_REPEAT:
            entry["reproduces_syntax_error"] = bool(
                result.get("http_status") == original.get(
                    "http_status"
                )
                and result.get("sqlite_error")
            )

    except Exception as exc:
        entry["state"] = "failed"
        entry["failure_category"] = (
            "evidence_integrity_failure"
            if isinstance(exc, BoundaryError)
            else "executor_failure"
        )

    return entry
