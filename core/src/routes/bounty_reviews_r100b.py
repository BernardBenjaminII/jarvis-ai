"""R10.0B: authenticated, human-gated opportunity reviews."""

from typing import Literal

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Path,
    Query,
)
from fastapi.security import HTTPBasicCredentials
from pydantic import BaseModel, Field

from core.bounty_agent.http_access import (
    basic,
    require_bounty_access,
)
from core.bounty_catalog.review_queue_r100b import (
    ReviewError,
    get_review_history,
    list_reviews,
    transition_review,
)


ReviewState = Literal[
    "pending",
    "acknowledged",
    "deferred",
    "resolved",
]

router = APIRouter(
    tags=["Bounty Opportunity Reviews"],
    dependencies=[Depends(require_bounty_access)],
)


class ReviewDecisionRequest(BaseModel):
    expected_state: ReviewState
    new_state: ReviewState
    request_id: str = Field(
        min_length=8,
        max_length=128,
        pattern=r"^[A-Za-z0-9._:-]+$",
    )
    note: str = Field(default="", max_length=400)


@router.get("/opportunity-reviews")
def opportunity_reviews(
    state: ReviewState | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        return list_reviews(
            state=state,
            limit=limit,
            offset=offset,
        )
    except ReviewError as exc:
        raise HTTPException(
            status_code=503,
            detail="Opportunity review queue unavailable",
        ) from exc


@router.get("/opportunity-reviews/{event_id}/history")
def opportunity_review_history(
    event_id: int = Path(ge=1),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        return get_review_history(
            event_id,
            limit=limit,
            offset=offset,
        )
    except ReviewError as exc:
        if str(exc) == "Unknown opportunity event":
            raise HTTPException(
                status_code=404,
                detail="Opportunity event not found",
            ) from exc

        raise HTTPException(
            status_code=503,
            detail="Review history unavailable",
        ) from exc


@router.post("/opportunity-reviews/{event_id}/decisions")
def decide_opportunity_review(
    decision: ReviewDecisionRequest,
    event_id: int = Path(ge=1),
    credentials: HTTPBasicCredentials | None = Depends(basic),
    review_intent: str | None = Header(
        default=None,
        alias="X-Jarvis-Review-Intent",
    ),
):
    # Additional browser-request safeguard, not a substitute
    # for the authenticated router dependency.
    if review_intent != "review-state-only":
        raise HTTPException(
            status_code=403,
            detail="Explicit review intent required",
        )

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        return transition_review(
            event_id,
            expected_state=decision.expected_state,
            new_state=decision.new_state,
            actor=credentials.username,
            request_id=decision.request_id,
            note=decision.note,
        )

    except ReviewError as exc:
        message = str(exc)

        if message == "Unknown opportunity event":
            code = 404
            detail = "Opportunity event not found"
        elif message in (
            "Operations ledger does not exist",
            "Unsafe ledger file",
            "Unsafe ledger directory",
            "Review transition could not be recorded",
        ):
            code = 503
            detail = "Review storage unavailable"
        else:
            code = 409
            detail = "Review decision rejected"

        raise HTTPException(
            status_code=code,
            detail=detail,
        ) from exc
