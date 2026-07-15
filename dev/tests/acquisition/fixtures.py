"""
Reusable fixtures for Acquisition subsystem verification.

These fixtures intentionally avoid filesystem, database, queue,
network, or provider dependencies.

All generated objects are deterministic.
"""

from __future__ import annotations

import hashlib

from knowledge_engine.acquisition.admission.models import (
    AdmissionAction,
    AdmissionContext,
    AdmissionDecision,
    PolicyEvaluation,
)

from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


DEFAULT_CONTENT = (
    b"JARVIS deterministic acquisition fixture"
)


def make_candidate(
    *,
    filename: str = "fixture.txt",
    extension: str = ".txt",
    candidate_type: str = "document",
    media_type: str = "text/plain",
    provider_id: str = "filesystem",
    content: bytes = DEFAULT_CONTENT,
) -> SourceCandidate:
    """
    Build one deterministic acquisition candidate.
    """

    checksum = hashlib.sha256(
        content
    ).hexdigest()

    return SourceCandidate(
        provider_id=provider_id,
        source_uri=f"file:///tmp/{filename}",
        local_path=f"/tmp/{filename}",
        filename=filename,
        extension=extension,
        media_type=media_type,
        candidate_type=candidate_type,
        size_bytes=len(content),
        checksum_sha256=checksum,
    )


def make_context(
    *,
    known_checksums=None,
    campaign_id=None,
):
    """
    Build one deterministic AdmissionContext.
    """

    return AdmissionContext(
        known_checksums=frozenset(
            known_checksums or ()
        ),
        campaign_id=campaign_id,
    )


def make_policy_evaluation(
    *,
    policy_id,
    priority,
    action,
    reason_code=None,
):
    """
    Build one deterministic policy evaluation.
    """

    return PolicyEvaluation(
        policy_id=policy_id,
        priority=priority,
        action=action,
        reason_code=(
            reason_code
            or f"{policy_id}_{action.value}"
        ),
        message=f"{policy_id} produced {action.value}",
        details={
            "fixture": True,
        },
    )


def make_accept_decision():

    candidate = make_candidate()

    return AdmissionDecision(
        candidate=candidate,
        evaluations=(
            make_policy_evaluation(
                policy_id="duplicate",
                priority=10,
                action=AdmissionAction.ACCEPT,
            ),
        ),
    )


def make_review_decision():

    candidate = make_candidate()

    return AdmissionDecision(
        candidate=candidate,
        evaluations=(
            make_policy_evaluation(
                policy_id="review",
                priority=10,
                action=AdmissionAction.REVIEW,
            ),
        ),
    )


def make_ignore_decision():

    candidate = make_candidate()

    return AdmissionDecision(
        candidate=candidate,
        evaluations=(
            make_policy_evaluation(
                policy_id="duplicate",
                priority=10,
                action=AdmissionAction.IGNORE,
            ),
        ),
    )


def make_reject_decision():

    candidate = make_candidate()

    return AdmissionDecision(
        candidate=candidate,
        evaluations=(
            make_policy_evaluation(
                policy_id="extension",
                priority=10,
                action=AdmissionAction.REJECT,
            ),
        ),
    )
