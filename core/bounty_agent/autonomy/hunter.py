"""R9.14A: offline autonomous bounty workflow prototype.

No external requests, scanning, or automatic disclosure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def discover_programs(catalog):
    """Normalize and rank supplied mock opportunities."""
    return sorted(
        catalog,
        key=lambda p: (-p.get("priority", 0), p["id"]),
    )


def authorized(program):
    """Fail closed unless explicit local authorization exists."""
    return (
        program.get("active") is True
        and program.get("authorization_verified") is True
        and program.get("simulation_only") is True
        and isinstance(program.get("scope"), list)
        and bool(program["scope"])
        and all(
            isinstance(target, str)
            and target.endswith(".example")
            for target in program["scope"]
        )
    )


def plan_mission(program):
    return {
        "program_id": program["id"],
        "targets": list(program["scope"]),
        "mode": "offline_simulation",
        "created_at": now(),
    }


def execute_mock_recon(mission):
    """Deterministic local observations, not vulnerability proof."""
    return [
        {
            "target": target,
            "observation": "simulated_http_response",
            "status_code": 200,
            "source": "mock_adapter",
        }
        for target in mission["targets"]
    ]


def analyze(observations):
    return [
        {
            "target": item["target"],
            "classification": "recon_observation",
            "validated_vulnerability": False,
            "evidence": item,
        }
        for item in observations
    ]


def run_cycle(catalog, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    programs = discover_programs(catalog)
    eligible = [p for p in programs if authorized(p)]

    if not eligible:
        return {
            "status": "no_eligible_programs",
            "missions": [],
        }

    selected = eligible[0]
    mission = plan_mission(selected)
    observations = execute_mock_recon(mission)
    findings = analyze(observations)

    report = {
        "schema": "jarvis.bounty.autonomy.r914a",
        "status": "awaiting_human_review",
        "program": selected["id"],
        "mission": mission,
        "observations": observations,
        "findings": findings,
        "confirmed_vulnerabilities": 0,
        "submission_authorized": False,
        "generated_at": now(),
    }

    content = json.dumps(
        report, indent=2, sort_keys=True
    ).encode("utf-8")

    digest = hashlib.sha256(content).hexdigest()
    path = output_dir / f"review-{digest[:16]}.json"
    path.write_bytes(content)

    return {
        "status": "awaiting_human_review",
        "missions": [mission],
        "report_path": str(path),
        "sha256": digest,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    catalog = json.loads(
        Path(args.catalog).read_text(encoding="utf-8")
    )
    if not isinstance(catalog, list):
        parser.error("Catalog must be a JSON list")

    result = run_cycle(catalog, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
