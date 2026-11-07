"""R9.18B: bounded, localhost-only autonomous lab executor."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from core.bounty_agent.autonomy.adaptive_planner_r918 import (
    plan_next,
)

HOST = "127.0.0.1"
PORT = 3000
ENDPOINT = "/rest/products/search"
MAX_BODY = 65536
MAX_REQUESTS = 5

# Approved, non-destructive local-lab diagnostic catalog.
# The planner selects capabilities; the executor owns request details.
CATALOG = {
    "baseline_http": ("baseline", "apple"),
    "sql_syntax_diagnostic": ("syntax", "apple'"),
    "boolean_comparison": ("comparison", "apple%"),
    "reproducibility_check": ("repeat_baseline", "apple"),
}

CAPABILITIES = frozenset(CATALOG)


class ExecutionBoundaryError(RuntimeError):
    pass


@dataclass(frozen=True)
class LocalMission:
    approved: bool
    target: str = f"http://{HOST}:{PORT}{ENDPOINT}"
    max_requests: int = MAX_REQUESTS


def validate_mission(mission: LocalMission) -> None:
    if not isinstance(mission, LocalMission):
        raise ExecutionBoundaryError("Invalid mission")

    if mission.approved is not True:
        raise ExecutionBoundaryError("Local-lab approval required")

    if mission.target != f"http://{HOST}:{PORT}{ENDPOINT}":
        raise ExecutionBoundaryError("Target outside approved scope")

    if (
        type(mission.max_requests) is not int
        or not 1 <= mission.max_requests <= MAX_REQUESTS
    ):
        raise ExecutionBoundaryError("Invalid request budget")


def execute_capability(capability: str) -> dict:
    """Execute one catalog entry against the fixed loopback endpoint."""

    if capability not in CATALOG:
        raise ExecutionBoundaryError("Unapproved capability")

    label, query = CATALOG[capability]
    connection = http.client.HTTPConnection(
        HOST, PORT, timeout=5
    )

    try:
        connection.connect()

        if connection.sock.getpeername() != (HOST, PORT):
            raise ExecutionBoundaryError("Unexpected network peer")

        path = ENDPOINT + "?" + urlencode({"q": query})

        connection.request(
            "GET",
            path,
            headers={"Connection": "close"},
        )

        response = connection.getresponse()
        status = response.status

        if 300 <= status < 400:
            raise ExecutionBoundaryError("Redirect rejected")

        body = response.read(MAX_BODY + 1)

        if len(body) > MAX_BODY:
            raise ExecutionBoundaryError("Response exceeds limit")

        try:
            payload = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            payload = None

        products = (
            payload.get("data")
            if isinstance(payload, dict)
            else None
        )

        valid = (
            status == 200
            and isinstance(payload, dict)
            and payload.get("status") == "success"
            and isinstance(products, list)
            and all(
                isinstance(item, dict)
                and type(item.get("id")) is int
                for item in products
            )
        )

        ids = (
            sorted({item["id"] for item in products})
            if valid else []
        )

        text = body.decode("utf-8", errors="replace")
        sql_error = (
            "SQLITE_ERROR" in text
            if status >= 400
            else False
        )

        return {
            "capability": capability,
            "probe": label,
            "http_status": status,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "query_sha256": hashlib.sha256(
                query.encode("utf-8")
            ).hexdigest(),
            "product_ids": ids,
            "product_count": len(products) if valid else None,
            "valid_product_response": valid,
            "sqlite_error": (
                "SQLite error observed" if sql_error else None
            ),
        }

    except (OSError, http.client.HTTPException) as exc:
        raise ExecutionBoundaryError(
            "Local-lab request failed"
        ) from exc
    finally:
        connection.close()


def run_mission(
    *,
    mission: LocalMission,
    evidence_dir: str | Path,
) -> dict:
    """Run a bounded adaptive mission and preserve its observations."""

    validate_mission(mission)

    output = Path(evidence_dir)

    if not output.is_dir() or output.is_symlink():
        raise ExecutionBoundaryError("Invalid evidence directory")

    observations = []
    planner_history = []
    completed = set()
    stop_reason = "request_budget_exhausted"

    try:
        for _ in range(mission.max_requests):
            remaining = CAPABILITIES - completed

            if not remaining:
                stop_reason = "capability_catalog_exhausted"
                break

            decision = plan_next(
                observations=observations,
                allowed_capabilities=frozenset(remaining),
                remaining_budget=mission.max_requests - len(observations),
            )

            if decision.action != "propose_test":
                stop_reason = decision.rationale
                break

            capability = decision.capability

            if capability not in remaining:
                raise ExecutionBoundaryError(
                    "Planner selected an unapproved capability"
                )

            # Record before execution, including failed attempts.
            entry = {
                "capability": capability,
                "rationale": decision.rationale,
                "state": "attempted",
            }
            observations.append(entry)
            completed.add(capability)

            result = execute_capability(capability)
            entry.update(result)
            entry["state"] = "completed"

            if capability == "baseline_http":
                planner_history.append({
                    "baseline_complete": result[
                        "valid_product_response"
                    ],
                })

                if not result["valid_product_response"]:
                    stop_reason = "invalid_baseline"
                    break

            elif capability == "sql_syntax_diagnostic":
                planner_history.append({
                    "sqlite_error": result["sqlite_error"],
                })

            elif capability == "boolean_comparison":
                baseline = next(
                    (
                        item for item in observations
                        if item["capability"] == "baseline_http"
                    ),
                    None,
                )

                different = (
                    baseline is not None
                    and result["valid_product_response"]
                    and result["product_ids"]
                    != baseline.get("product_ids")
                )

                planner_history.append({
                    "behavioral_difference": bool(different),
                })

            else:
                planner_history.append({
                    "baseline_complete": False,
                })

    except Exception as exc:
        stop_reason = (
            "execution_boundary_failure"
            if isinstance(exc, ExecutionBoundaryError)
            else "execution_failure"
        )
        # Preserve the failure type, not potentially sensitive details.
        if observations:
            observations[-1]["state"] = "failed"

    report = {
        "schema": "jarvis.bounty.adaptive_execution.r918b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": mission.target,
        "authorization": {
            "caller_approved": True,
            "independently_authenticated": False,
            "scope": "fixed_localhost_lab",
        },
        "request_count": len(observations),
        "request_budget": mission.max_requests,
        "observations": observations,
        "stop_reason": stop_reason,
        "classification": "diagnostic_observations_only",
        "validated_vulnerability": False,
        "human_review_required": True,
        "submission_authorized": False,
    }

    encoded = json.dumps(
        report, sort_keys=True, indent=2, allow_nan=False
    ).encode("utf-8")

    digest = hashlib.sha256(encoded).hexdigest()
    path = output / f"adaptive-r918b-{digest[:16]}.json"

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW

    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise ExecutionBoundaryError("Evidence collision") from exc

    with os.fdopen(fd, "wb") as handle:
        handle.write(encoded)

    return {
        "classification": report["classification"],
        "stop_reason": stop_reason,
        "request_count": len(observations),
        "observations": observations,
        "evidence_path": str(path),
        "sha256": digest,
    }
