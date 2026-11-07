
"""R9.16A: approved mission, offline simulation only."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from core.bounty_agent.autonomy.coordinator import coordinate_mission
from core.bounty_agent.autonomy.hunter import (
    execute_mock_recon,
    analyze,
)
from core.bounty_agent.report_export import (
    export_json,
    export_markdown,
)

from core.bounty_agent.autonomy.recon_planner import (
    build_recon_plan,
)

from core.bounty_agent.autonomy.investigation_strategy import (
    build_strategy,
)

from core.bounty_agent.autonomy.opportunity_scoring import (
    score_opportunities,
)

class MissionCycleError(RuntimeError):
    pass


def run_offline_cycle(
    *,
    proposal_store,
    approval_store,
    claim_store,
    agent,
    proposal_id,
    approval_id,
    output_dir,
):
    proposal = proposal_store.get(proposal_id)

    if (
        proposal is None
        or proposal["status"] != "pending"
        or time.time() >= proposal["expires"]
    ):
        raise MissionCycleError("Proposal not pending or expired")

    fields = {
        "authorization": proposal["authorization_id"],
        "program": proposal["program"],
        "target": proposal["target"],
        "policy_digest": proposal["policy_digest"],
        "budget": proposal["budget"],
    }

    if approval_store.verify(approval_id, **fields) is not True:
        raise MissionCycleError("Approval verification failed")

    if not proposal["target"].endswith(".example"):
        raise MissionCycleError(
            "Offline simulation requires a .example target"
        )

    coordinated = coordinate_mission(
        claim_store=claim_store,
        agent=agent,
        approval_store=approval_store,
        approval_id=approval_id,
        **fields,
    )

    if coordinated.status not in {
        "mission_created",
        "already_created",
    }:
        raise MissionCycleError("Unexpected coordination state")

    session_id = coordinated.session_id
    mission_id = coordinated.mission_id


    recon_plan = build_recon_plan(
        authorization_store=agent.authorization_store,
        authorization_id=proposal["authorization_id"],
        program=proposal["program"],
        target=proposal["target"],
        budget=proposal["budget"],
    )

    report = agent.report(session_id)

    if (
        report["session"]["authorization"]
        != proposal["authorization_id"]
        or report["session"]["root_target"]
        != proposal["target"]
    ):
        raise MissionCycleError("Report ownership mismatch")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # The simulation never creates live reconnaissance tasks.
    simulation = {
        "targets": [proposal["target"]],
        "mode": "offline_simulation",
    }

    observations = execute_mock_recon(simulation)
    findings = analyze(observations)

    strategy = build_strategy(
        artifact={
            "simulation_only": True,
            "authorization_id": proposal["authorization_id"],
            "recon_plan": recon_plan,
            "findings": findings,
        }
    )


    selected_capabilities = [
        task["capability"]
        for task in recon_plan["tasks"]
    ]

    scoring_inputs = [
        {
            "target": finding["target"],
            "simulation_only": True,
            "validated_vulnerability": False,
            "evidence": finding["evidence"],
            "evidence_quality": 0,
            "investigation_value": 1,
            "estimated_effort": 1,
            "required_capability": "http_probe",
        }
        for finding in findings
    ]

    opportunity_scoring = score_opportunities(
        opportunities=scoring_inputs,
        authorized_target=proposal["target"],
        available_capabilities=selected_capabilities,
        budget=proposal["budget"],
    )
    payload = {
        "schema": "jarvis.bounty.mission_cycle.r916a",
        "simulation_only": True,
	"recon_plan": recon_plan,
	"investigation_strategy": strategy,
        "opportunity_scoring": opportunity_scoring,
	"submission_authorized": False,
        "validated_vulnerabilities": 0,
        "proposal_id": proposal_id,
        "approval_id": approval_id,
        "authorization_id": proposal["authorization_id"],
        "session_id": session_id,
        "mission_id": mission_id,
        "observations": observations,
        "findings": findings,
        "investigation_report": json.loads(
            export_json(report)
        ),
    }

    content = json.dumps(
        payload,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ).encode("utf-8")

    digest = hashlib.sha256(content).hexdigest()
    path = output / f"mission-cycle-{digest[:16]}.json"

    if not path.exists():
        path.write_bytes(content)

    markdown = output / f"mission-cycle-{digest[:16]}.md"

    if not markdown.exists():
        markdown.write_text(
            export_markdown(report),
            encoding="utf-8",
        )

    return {
        "status": "awaiting_human_review",
        "simulation_only": True,
        "session_id": session_id,
        "mission_id": mission_id,
        "report_path": str(path),
        "markdown_path": str(markdown),
        "sha256": digest,
    }
