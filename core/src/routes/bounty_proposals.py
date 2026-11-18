"""R9.15A.5: read-only bounty proposal API."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from core.bounty_agent.http_access import require_bounty_access
from core.bounty_agent.autonomy.proposals import ProposalStore


router = APIRouter(
    prefix="/api/bounty-agent/proposals",
    tags=["bounty-proposals"],
    dependencies=[Depends(require_bounty_access)],
)


def proposal_store():
    root = os.environ.get("JARVIS_RUNTIME_ROOT")

    if root:
        path = Path(root) / "bounty_agent" / "proposals.sqlite"
    else:
        path = (
            Path.home()
            / ".local/share/jarvis/bounty_agent/proposals.sqlite"
        )

    return ProposalStore(path)


@router.get("")
def list_proposals():
    return {
        "proposals": proposal_store().pending(),
    }


@router.get("/{proposal_id}")
def get_proposal(proposal_id: str):
    record = proposal_store().get(proposal_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Proposal not found",
        )

    return record


# R9.15A.7 planning-only endpoint

from core.bounty_catalog.store import Catalog
from core.bounty_authorization.store import AuthorizationStore
from core.bounty_agent.autonomy.orchestrator import (
    queue_mission_proposal,
)


def production_catalog():
    root = Path(
        os.environ.get(
            "JARVIS_RUNTIME_ROOT",
            str(Path.home() / ".local/share/jarvis"),
        )
    ).expanduser()

    path = root / "bounty_catalog" / "r4.sqlite"

    # Never silently create an empty production catalog.
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Bounty program catalog unavailable",
        )

    return Catalog(path)


@router.post("/plan")
def plan_proposal():
    catalog = production_catalog()
    authorization_store = AuthorizationStore()

    # Planning is disabled if no active reviewed
    # authorization exists.
    from core.bounty_agent.autonomy.catalog_controller import (
        existing_authorizations,
    )

    records = existing_authorizations(
        authorization_store
    )

    if not records:
        return {
            "status": "no_authorized_candidate",
            "proposal": None,
        }

    # Derive a stable digest from existing reviewed
    # authorization evidence, never from browser input.
    import hashlib
    import json

    evidence = sorted(
        (
            record["id"],
            record["scope_json"],
        )
        for record in records
    )

    digest = hashlib.sha256(
        json.dumps(
            evidence,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return queue_mission_proposal(
        catalog=catalog,
        authorization_store=authorization_store,
        proposal_store=proposal_store(),
        policy_digest=digest,
        budget=2,
        ttl=3600,
    )
