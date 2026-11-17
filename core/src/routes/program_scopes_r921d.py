"""R9.21D2: program-scope draft API.

Must be mounted under the existing authenticated Bounty router.
No reviewer approvals, network reconnaissance, or execution.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.bounty_agent.autonomy.program_scope_r921a import (
    ScopeIntakeError,
    create_scope_draft,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
    ProgramScopeStoreError,
)

router = APIRouter(tags=["Bounty Program Scopes"])


class ImportScopeRequest(BaseModel):
    platform: Literal["hackerone", "bugcrowd", "intigriti"]
    program: str = Field(min_length=1, max_length=200)
    policy_url: str = Field(min_length=1, max_length=1000)
    in_scope: list[str] = Field(
        min_length=1, max_length=200
    )
    out_of_scope: list[str] = Field(
        default_factory=list, max_length=200
    )
    restrictions: list[str] = Field(
        min_length=1, max_length=100
    )


def _store():
    base = Path(
        os.environ.get(
            "XDG_DATA_HOME",
            str(Path.home() / ".local" / "share"),
        )
    ).expanduser()

    return ProgramScopeStore(
        base / "jarvis" / "program_scopes_r921d.sqlite3"
    )


@router.get("/program-scopes")
def list_program_scopes(
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        return {
            "schema": "jarvis.bounty.scope_list.r921d2",
            "drafts": _store().list_drafts(limit),
            "execution_authorized": False,
        }
    except (ProgramScopeStoreError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Program scope store unavailable",
        ) from exc


@router.get("/program-scopes/{draft_id}")
def get_program_scope(draft_id: str):
    if len(draft_id) > 100:
        raise HTTPException(
            status_code=404,
            detail="Policy draft not found",
        )

    try:
        return _store().get_draft(draft_id)
    except ProgramScopeStoreError as exc:
        if str(exc) == "Unknown policy draft":
            raise HTTPException(
                status_code=404,
                detail="Policy draft not found",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail="Program scope store unavailable",
        ) from exc


@router.post("/program-scopes", status_code=201)
def import_program_scope(request: ImportScopeRequest):
    # Apply tighter limits before persisting the data.
    collections = (
        request.in_scope,
        request.out_of_scope,
        request.restrictions,
    )

    if any(
        not isinstance(item, str) or len(item) > 1000
        for collection in collections
        for item in collection
    ):
        raise HTTPException(
            status_code=422,
            detail="Policy item exceeds length limit",
        )

    try:
        draft = create_scope_draft(
            platform=request.platform,
            program=request.program,
            policy_url=request.policy_url,
            in_scope=request.in_scope,
            out_of_scope=request.out_of_scope,
            restrictions=request.restrictions,
        )

        draft_id = _store().import_draft(draft)

    except (ScopeIntakeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Invalid program scope data",
        ) from exc
    except (ProgramScopeStoreError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Program scope store unavailable",
        ) from exc

    return {
        "id": draft_id,
        "policy_sha256": draft["policy_sha256"],
        "review_status": "unverified",
        "scope_verified": False,
        "execution_authorized": False,
        "submission_authorized": False,
    }
