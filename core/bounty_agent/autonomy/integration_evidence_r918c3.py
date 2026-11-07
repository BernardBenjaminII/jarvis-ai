"""R9.18C.3: persistent evidence for bounded local investigations."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path

from core.bounty_agent.autonomy.adaptive_executor_r918 import (
    HOST, PORT, ENDPOINT, MAX_REQUESTS, CATALOG,
)
from core.bounty_agent.autonomy.adaptive_integration_r918c3 import (
    IntegratedResult, SYNTAX_REPEAT,
)


class EvidenceError(ValueError):
    pass


def persist(
    *,
    result: IntegratedResult,
    evidence_dir: str | Path,
) -> dict:
    """Persist one completed local-lab investigation."""

    if not isinstance(result, IntegratedResult):
        raise EvidenceError("Invalid integration result")

    if (
        result.request_count != len(result.observations)
        or result.request_count > MAX_REQUESTS
        or result.request_count < 0
    ):
        raise EvidenceError("Invalid request count")

    if (
        result.validated_vulnerability is not False
        or result.human_review_required is not True
        or result.submission_authorized is not False
    ):
        raise EvidenceError("Unsafe assessment flags")

    observations = [dict(item) for item in result.observations]

    if any(
        item.get("state") not in {"attempted", "completed", "failed"}
        for item in observations
    ):
        raise EvidenceError("Invalid observation state")

    from core.bounty_agent.autonomy.experiment_planner_r918c2 import (
        EXPERIMENTS,
    )

    seen = set()

    for index, item in enumerate(observations):
        capability = item.get("capability")

        if not isinstance(capability, str):
            raise EvidenceError("Invalid capability")

        if capability in seen:
            raise EvidenceError("Duplicate experiment")

        seen.add(capability)

        execution_capability = (
            "sql_syntax_diagnostic"
            if capability == SYNTAX_REPEAT
            else capability
        )

        if execution_capability not in CATALOG:
            raise EvidenceError("Unknown experiment")

        expected_identity = (
            "repeat_syntax_apple_quote"
            if capability == SYNTAX_REPEAT
            else EXPERIMENTS[capability].identity
        )

        if item.get("experiment_identity") != expected_identity:
            raise EvidenceError("Experiment identity mismatch")

        if item["state"] == "completed":
            expected_hash = hashlib.sha256(
                CATALOG[execution_capability][1].encode("utf-8")
            ).hexdigest()

            if item.get("query_sha256") != expected_hash:
                raise EvidenceError("Canonical query hash mismatch")

        if capability == SYNTAX_REPEAT:
            if "sql_syntax_diagnostic" not in seen:
                raise EvidenceError("Syntax repetition without diagnostic")

            if index == 0:
                raise EvidenceError("Invalid experiment ordering")

    if observations:
        if observations[0].get("capability") != "baseline_http":
            raise EvidenceError("Missing initial baseline")

    for index, item in enumerate(observations):
        state = item["state"]

        if state == "attempted":
            raise EvidenceError("Unresolved attempted experiment")

        if state == "failed":
            if index != len(observations) - 1:
                raise EvidenceError("Experiment after failure")

            if item.get("failure_category") not in {
                "executor_failure",
                "evidence_integrity_failure",
            }:
                raise EvidenceError("Missing failure classification")

        if state == "completed":
            if (
                not isinstance(item.get("http_status"), int)
                or isinstance(item.get("http_status"), bool)
                or not 100 <= item["http_status"] <= 599
            ):
                raise EvidenceError("Invalid HTTP status")

        if item.get("capability") == SYNTAX_REPEAT:
            original = next(
                (
                    earlier for earlier in observations[:index]
                    if earlier.get("capability")
                    == "sql_syntax_diagnostic"
                    and earlier.get("state") == "completed"
                ),
                None,
            )

            if original is None:
                raise EvidenceError("Missing completed syntax diagnostic")

            original_signal = (
                original.get("http_status") == 500
                and bool(original.get("sqlite_error"))
            )

            if not original_signal:
                raise EvidenceError(
                    "Syntax repetition lacks diagnostic signal"
                )

            if state == "completed":
                observed_reproduction = (
                    item.get("http_status") == 500
                    and bool(item.get("sqlite_error"))
                    and item.get("query_sha256")
                    == original.get("query_sha256")
                )

                if (
                    item.get("reproduces_syntax_error")
                    is not observed_reproduction
                ):
                    raise EvidenceError(
                        "Contradictory reproduction assessment"
                    )

    syntax = next(
        (
            item for item in observations
            if item.get("capability") == "sql_syntax_diagnostic"
            and item.get("state") == "completed"
        ),
        None,
    )

    repetition = next(
        (
            item for item in observations
            if item.get("capability") == "syntax_repetition"
            and item.get("state") == "completed"
        ),
        None,
    )

    reproduced = bool(
        syntax
        and repetition
        and syntax.get("query_sha256")
        and syntax.get("query_sha256")
        == repetition.get("query_sha256")
        and syntax.get("http_status") == 500
        and repetition.get("http_status") == 500
        and syntax.get("sqlite_error")
        and repetition.get("sqlite_error")
    )

    report = {
        "schema": "jarvis.bounty.adaptive_execution.r918c3",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target": f"http://{HOST}:{PORT}{ENDPOINT}",
        "authorization": {
            "caller_approved": True,
            "independently_authenticated": False,
            "scope": "fixed_localhost_lab",
        },
        "request_count": result.request_count,
        "request_budget_ceiling": MAX_REQUESTS,
        "stop_reason": result.stop_reason,
        "observations": observations,
        "assessment": {
            "classification": (
                "reproduced_sql_diagnostic"
                if reproduced
                else "inconclusive_diagnostic"
            ),
            "syntax_condition_reproduced": reproduced,
            "validated_vulnerability": False,
            "human_review_required": True,
            "submission_authorized": False,
        },
    }

    encoded = json.dumps(
        report,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8")

    digest = hashlib.sha256(encoded).hexdigest()
    filename = f"adaptive-r918c3-{digest[:16]}.json"

    directory = Path(evidence_dir)

    # Reject symlinks and open the directory itself so the
    # final file is created relative to the verified directory.
    if directory.is_symlink() or not directory.is_dir():
        raise EvidenceError("Invalid evidence directory")

    dir_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_fd = os.open(directory, dir_flags)

    try:
        info = os.fstat(directory_fd)

        if not stat.S_ISDIR(info.st_mode):
            raise EvidenceError("Evidence destination is not a directory")

        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
        )

        fd = os.open(
            filename,
            flags,
            0o600,
            dir_fd=directory_fd,
        )

        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())

        os.fsync(directory_fd)

    finally:
        os.close(directory_fd)

    return {
        "evidence_path": str(directory / filename),
        "sha256": digest,
        "classification": report["assessment"]["classification"],
        "request_count": result.request_count,
        "syntax_condition_reproduced": reproduced,
        "validated_vulnerability": False,
    }
