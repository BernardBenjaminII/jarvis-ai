"""R9.21E4: authenticated, nonexecuting scope review API."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel, Field

from core.bounty_agent.http_access import (
    basic,
    require_bounty_access,
)
from core.bounty_agent.autonomy.program_scope_store_r921d import (
    ProgramScopeStore,
    ProgramScopeStoreError,
)
from core.bounty_agent.autonomy.program_scope_reviews_r921e3 import (
    ScopeReviewStore,
    ScopeReviewStoreError,
)
from core.bounty_agent.autonomy.program_scope_review_r921b import (
    ScopeReviewError,
)
from core.bounty_agent.autonomy.program_scope_bridge_r921e import (
    assess_authorization_binding,
)
from core.bounty_authorization.store import AuthorizationStore


router = APIRouter(tags=["Bounty Scope Reviews"])


def authenticated_reviewer(
    _validated=Depends(require_bounty_access),
    credentials: HTTPBasicCredentials | None = Depends(basic),
):
    # require_bounty_access validates the same request credentials.
    # Do not use a reviewer name supplied in request JSON.
    if credentials is None:
        raise HTTPException(status_code=401)

    return credentials.username


def _data_dir():
    root = Path(
        os.environ.get(
            "XDG_DATA_HOME",
            str(Path.home() / ".local" / "share"),
        )
    ).expanduser()

    return root / "jarvis"


def _draft_store():
    return ProgramScopeStore(
        _data_dir() / "program_scopes_r921d.sqlite3"
    )


def _review_store():
    return ScopeReviewStore(
        _data_dir() / "program_scope_reviews_r921e3.sqlite3"
    )


def _load_draft(draft_id):
    if not isinstance(draft_id, str) or len(draft_id) > 100:
        raise HTTPException(404, "Policy draft not found")

    try:
        return _draft_store().get_draft(draft_id)["draft"]
    except ProgramScopeStoreError as exc:
        if str(exc) == "Unknown policy draft":
            raise HTTPException(
                404, "Policy draft not found"
            ) from exc

        raise HTTPException(
            503, "Policy draft store unavailable"
        ) from exc


class ReviewRequest(BaseModel):
    source_checked_at: str = Field(min_length=1, max_length=80)
    source_matches: bool


class AssessmentRequest(BaseModel):
    review_id: str = Field(min_length=1, max_length=100)
    hostname: str = Field(min_length=1, max_length=253)
    authorization_id: str = Field(min_length=1, max_length=100)


@router.post(
    "/program-scopes/{draft_id}/reviews",
    status_code=201,
)
def create_scope_review(
    draft_id: str,
    request: ReviewRequest,
    reviewer: str = Depends(authenticated_reviewer),
):
    try:
        draft = _load_draft(draft_id)

        return _review_store().attest(
            draft_id=draft_id,
            draft=draft,
            reviewer=reviewer,
            source_checked_at=request.source_checked_at,
            source_matches=request.source_matches,
        )
    except (ScopeReviewError, ValueError) as exc:
        raise HTTPException(
            422, "Invalid source-review attestation"
        ) from exc
    except (ScopeReviewStoreError, OSError) as exc:
        raise HTTPException(
            503, "Scope review store unavailable"
        ) from exc


@router.get(
    "/program-scopes/{draft_id}/reviews/{review_id}",
)
def get_scope_review(
    draft_id: str,
    review_id: str,
    _reviewer: str = Depends(authenticated_reviewer),
):
    if len(review_id) > 100:
        raise HTTPException(404, "Review not found")

    draft = _load_draft(draft_id)

    try:
        return _review_store().get(
            review_id,
            draft_id=draft_id,
            draft=draft,
        )
    except ScopeReviewStoreError as exc:
        if str(exc) == "Unknown review":
            raise HTTPException(404, "Review not found") from exc

        raise HTTPException(
            409, "Review is invalid or expired"
        ) from exc
    except (OSError, ValueError) as exc:
        raise HTTPException(
            503, "Scope review store unavailable"
        ) from exc


@router.post(
    "/program-scopes/{draft_id}/authorization-assessment",
)
def assess_existing_authorization(
    draft_id: str,
    request: AssessmentRequest,
    _reviewer: str = Depends(authenticated_reviewer),
):
    draft = _load_draft(draft_id)

    try:
        stored = _review_store().get(
            request.review_id,
            draft_id=draft_id,
            draft=draft,
        )
    except ScopeReviewStoreError:
        raise HTTPException(
            409, "Review unavailable, invalid, or expired"
        ) from None

    try:
        result = assess_authorization_binding(
            draft=draft,
            review=stored["review"],
            hostname=request.hostname,
            authorization_id=request.authorization_id,
            authorization_store=AuthorizationStore(),
        )
    except (OSError, ValueError):
        raise HTTPException(
            503, "Authorization store unavailable"
        ) from None

    return {
        **result,
        "execution_authorized": False,
        "submission_authorized": False,
        "execution_started": False,
    }
