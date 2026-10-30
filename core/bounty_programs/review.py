from __future__ import annotations

import hashlib
import json

from .model import (
    ProgramIntakeDraft,
    ProgramScopeError,
    ProgramSnapshot,
)
from .normalize import normalize_assets
from .store import ProgramStore


class ProgramReviewError(ProgramScopeError):
    pass


def _draft_source_material(
    draft: dict,
) -> str:
    """
    Reconstruct the exact source material used by R9.0B
    ProgramIntakeDraft.from_catalog_record() when calculating
    source_digest.
    """

    return json.dumps(
        {
            "source":
                draft.get("source"),
            "handle":
                draft.get("handle"),
            "name":
                draft.get("name"),
            "program_url":
                draft.get("program_url"),
            "reward_status":
                draft.get("reward_status"),
            "submission_state":
                draft.get("submission_state"),
            "visibility":
                draft.get("visibility"),
            "policy_text":
                draft.get("policy_text") or "",
            "source_updated_at":
                draft.get("source_updated_at"),
            "source_page_url":
                draft.get("source_page_url"),
            "source_page_sha256":
                draft.get("source_page_sha256"),
            "source_run_id":
                draft.get("source_run_id"),
            "observed_at":
                draft.get("observed_at"),
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def verify_draft_integrity(
    stored: dict,
) -> dict:
    draft = stored.get("draft")

    if not isinstance(draft, dict):
        raise ProgramReviewError(
            "Stored draft payload is invalid"
        )

    stored_digest = str(
        stored.get("source_digest") or ""
    )

    embedded_digest = str(
        draft.get("source_digest") or ""
    )

    if not stored_digest:
        raise ProgramReviewError(
            "Draft is missing stored source digest"
        )

    if embedded_digest != stored_digest:
        raise ProgramReviewError(
            "Draft source digest does not match "
            "the stored record"
        )

    source_material = _draft_source_material(
        draft
    )

    recomputed = hashlib.sha256(
        source_material.encode()
    ).hexdigest()

    if recomputed != stored_digest:
        raise ProgramReviewError(
            "Draft source provenance verification failed"
        )

    if (
        draft.get("testing_authorized")
        is not False
        or draft.get("execution_enabled")
        is not False
    ):
        raise ProgramReviewError(
            "Draft must remain non-executable "
            "before scope review"
        )

    if (
        draft.get("structured_scope_reviewed")
        is not False
    ):
        raise ProgramReviewError(
            "Draft has already crossed an invalid "
            "review boundary"
        )

    return draft


def review_draft(
    *,
    store: ProgramStore,
    draft_id: str,
    reviewer: str,
    include,
    exclude=(),
    acknowledge_policy_review: bool,
) -> tuple[str, ProgramSnapshot]:

    reviewer = str(reviewer).strip()

    if not reviewer:
        raise ProgramReviewError(
            "Reviewer identity is required"
        )

    if not acknowledge_policy_review:
        raise ProgramReviewError(
            "Policy review must be explicitly acknowledged"
        )

    stored = store.get_draft(
        draft_id
    )

    draft = verify_draft_integrity(
        stored
    )

    if draft.get("stale"):
        raise ProgramReviewError(
            "Refusing to review a stale catalog draft; "
            "refresh the HackerOne catalog first"
        )

    if draft.get("submission_state") != "open":
        raise ProgramReviewError(
            "Program is not currently open for submissions"
        )

    include = tuple(include or ())
    exclude = tuple(exclude or ())

    if not include:
        raise ProgramReviewError(
            "At least one explicit in-scope asset "
            "is required"
        )

    assets = normalize_assets(
        in_scope=include,
        out_of_scope=exclude,
    )

    # Reject contradictory exact entries.
    normalized_include = {
        asset.normalized
        for asset in assets
        if asset.eligible
    }

    normalized_exclude = {
        asset.normalized
        for asset in assets
        if not asset.eligible
    }

    overlap = (
        normalized_include
        & normalized_exclude
    )

    if overlap:
        raise ProgramReviewError(
            "Assets cannot be both included and excluded: "
            + ", ".join(sorted(overlap))
        )

    review_material = json.dumps(
        {
            "schema":
                "jarvis-bounty-program-review-r9.0c",
            "source_draft_id":
                draft_id,
            "source_draft_digest":
                draft["source_digest"],
            "reviewer":
                reviewer,
            "program":
                draft["handle"],
            "program_url":
                draft["program_url"],
            "policy_text":
                draft.get("policy_text") or "",
            "include":
                sorted(normalized_include),
            "exclude":
                sorted(normalized_exclude),
            "policy_review_acknowledged":
                True,
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    snapshot = ProgramSnapshot.reviewed_input(
        source="hackerone",
        handle=draft["handle"],
        name=draft["name"],
        source_url=draft["program_url"],
        assets=assets,
        rules_text=(
            draft.get("policy_text")
            or ""
        ),
        source_material=review_material,
        reviewer=reviewer,
        source_draft_id=draft_id,
        source_draft_digest=(
            draft["source_digest"]
        ),
        structured_scope_reviewed=True,
    )

    program_id = store.save(
        snapshot
    )

    return program_id, snapshot
