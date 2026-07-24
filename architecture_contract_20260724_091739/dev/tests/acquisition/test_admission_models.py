"""
Focused contracts for JARVIS acquisition-admission models.

This suite verifies:

- canonical admission actions
- immutable model behavior
- deterministic serialization
- deterministic fingerprints
- policy-evaluation validation
- decision precedence
- deterministic evaluation ordering
- convenience properties
- SourceCandidate serialization fallback behavior

No filesystem, database, queue, or network access occurs.
"""

from __future__ import annotations

import hashlib
from dataclasses import FrozenInstanceError

from knowledge_engine.acquisition.admission.models import (
    AdmissionAction,
    AdmissionContext,
    AdmissionDecision,
    PolicyEvaluation,
)
from knowledge_engine.acquisition.models import (
    SourceCandidate,
)


def create_candidate(
    *,
    filename: str = "manual.txt",
    extension: str = ".txt",
    candidate_type: str = "document",
    content: bytes = b"JARVIS admission model fixture",
) -> SourceCandidate:
    """Create one deterministic acquisition candidate."""

    checksum = hashlib.sha256(
        content
    ).hexdigest()

    return SourceCandidate(
        provider_id="filesystem",
        source_uri=f"file:///tmp/{filename}",
        local_path=f"/tmp/{filename}",
        filename=filename,
        extension=extension,
        media_type="text/plain",
        candidate_type=candidate_type,
        size_bytes=len(content),
        checksum_sha256=checksum,
    )


def create_evaluation(
    *,
    policy_id: str,
    priority: int,
    action: AdmissionAction,
    reason_code: str | None = None,
    message: str | None = None,
) -> PolicyEvaluation:
    """Create one deterministic policy evaluation."""

    return PolicyEvaluation(
        policy_id=policy_id,
        priority=priority,
        action=action,
        reason_code=(
            reason_code
            or f"{policy_id}_reason"
        ),
        message=(
            message
            or f"{policy_id} produced {action.value}"
        ),
        details={
            "fixture": True,
            "policy": policy_id,
        },
    )


def assert_frozen(
    instance: object,
    attribute_name: str,
    replacement: object,
) -> None:
    """Assert that a frozen dataclass rejects mutation."""

    try:
        setattr(
            instance,
            attribute_name,
            replacement,
        )
    except FrozenInstanceError:
        return

    raise AssertionError(
        f"{type(instance).__name__} must remain immutable"
    )


def verify_admission_action_contract() -> None:
    """Verify canonical action names and string values."""

    assert tuple(
        action.name
        for action in AdmissionAction
    ) == (
        "ACCEPT",
        "REVIEW",
        "IGNORE",
        "REJECT",
    )

    assert tuple(
        action.value
        for action in AdmissionAction
    ) == (
        "accept",
        "review",
        "ignore",
        "reject",
    )

    assert AdmissionAction("accept") is AdmissionAction.ACCEPT
    assert AdmissionAction("review") is AdmissionAction.REVIEW
    assert AdmissionAction("ignore") is AdmissionAction.IGNORE
    assert AdmissionAction("reject") is AdmissionAction.REJECT

    print("[PASS] AdmissionAction canonical contract")


def verify_context_contract() -> None:
    """Verify context normalization, serialization, and immutability."""

    checksum_a = "a" * 64
    checksum_b = "b" * 64

    context = AdmissionContext(
        known_checksums=frozenset({
            checksum_b,
            checksum_a,
            checksum_b,
        }),
        campaign_id="campaign-001",
        metadata={
            "source": "filesystem",
            "mode": "test",
        },
    )

    assert context.known_checksums == frozenset({
        checksum_a,
        checksum_b,
    })

    serialized = context.to_dict()

    assert serialized == {
        "known_checksums": [
            checksum_a,
            checksum_b,
        ],
        "campaign_id": "campaign-001",
        "metadata": {
            "source": "filesystem",
            "mode": "test",
        },
    }

    assert len(context.fingerprint) == 64
    assert context.fingerprint == AdmissionContext(
        known_checksums=frozenset({
            checksum_a,
            checksum_b,
        }),
        campaign_id="campaign-001",
        metadata={
            "mode": "test",
            "source": "filesystem",
        },
    ).fingerprint

    assert_frozen(
        context,
        "campaign_id",
        "changed",
    )

    print("[PASS] AdmissionContext serialization")
    print("[PASS] AdmissionContext deterministic fingerprint")
    print("[PASS] AdmissionContext immutable contract")


def verify_policy_evaluation_contract() -> None:
    """Verify evaluation serialization, validation, and fingerprinting."""

    evaluation = create_evaluation(
        policy_id="extension",
        priority=20,
        action=AdmissionAction.ACCEPT,
        reason_code="accepted_extension",
        message="Extension is approved.",
    )

    assert evaluation.to_dict() == {
        "policy_id": "extension",
        "priority": 20,
        "action": "accept",
        "reason_code": "accepted_extension",
        "message": "Extension is approved.",
        "details": {
            "fixture": True,
            "policy": "extension",
        },
    }

    repeated = create_evaluation(
        policy_id="extension",
        priority=20,
        action=AdmissionAction.ACCEPT,
        reason_code="accepted_extension",
        message="Extension is approved.",
    )

    assert evaluation == repeated
    assert evaluation.fingerprint == repeated.fingerprint
    assert len(evaluation.fingerprint) == 64

    assert_frozen(
        evaluation,
        "priority",
        999,
    )

    invalid_cases = (
        {
            "policy_id": "",
            "priority": 10,
            "action": AdmissionAction.ACCEPT,
            "reason_code": "valid",
            "message": "Valid message",
        },
        {
            "policy_id": "policy",
            "priority": -1,
            "action": AdmissionAction.ACCEPT,
            "reason_code": "valid",
            "message": "Valid message",
        },
        {
            "policy_id": "policy",
            "priority": 10,
            "action": AdmissionAction.ACCEPT,
            "reason_code": "",
            "message": "Valid message",
        },
        {
            "policy_id": "policy",
            "priority": 10,
            "action": AdmissionAction.ACCEPT,
            "reason_code": "valid",
            "message": "",
        },
    )

    for values in invalid_cases:
        try:
            PolicyEvaluation(**values)
        except ValueError:
            continue

        raise AssertionError(
            "Invalid PolicyEvaluation was accepted: "
            f"{values}"
        )

    print("[PASS] PolicyEvaluation serialization")
    print("[PASS] PolicyEvaluation deterministic fingerprint")
    print("[PASS] PolicyEvaluation validation")
    print("[PASS] PolicyEvaluation immutable contract")


def verify_accept_decision() -> None:
    """Verify the normal all-accept decision."""

    candidate = create_candidate()

    evaluations = (
        create_evaluation(
            policy_id="classification",
            priority=40,
            action=AdmissionAction.ACCEPT,
        ),
        create_evaluation(
            policy_id="exact_duplicate",
            priority=10,
            action=AdmissionAction.ACCEPT,
        ),
        create_evaluation(
            policy_id="size",
            priority=30,
            action=AdmissionAction.ACCEPT,
        ),
        create_evaluation(
            policy_id="extension",
            priority=20,
            action=AdmissionAction.ACCEPT,
        ),
    )

    decision = AdmissionDecision(
        candidate=candidate,
        evaluations=evaluations,
    )

    assert tuple(
        evaluation.policy_id
        for evaluation in decision.evaluations
    ) == (
        "exact_duplicate",
        "extension",
        "size",
        "classification",
    )

    assert decision.action is AdmissionAction.ACCEPT
    assert decision.accepted is True
    assert decision.requires_review is False
    assert decision.ignored is False
    assert decision.rejected is False
    assert decision.terminal is False

    serialized = decision.to_dict()

    assert serialized["action"] == "accept"
    assert serialized["candidate"]["filename"] == "manual.txt"
    assert len(serialized["evaluations"]) == 4
    assert len(decision.fingerprint) == 64

    assert str(decision) == (
        "AdmissionDecision("
        "action=accept, evaluations=4)"
    )

    assert_frozen(
        decision,
        "evaluations",
        (),
    )

    print("[PASS] AdmissionDecision deterministic ordering")
    print("[PASS] AdmissionDecision accept semantics")
    print("[PASS] AdmissionDecision serialization")
    print("[PASS] AdmissionDecision immutable contract")


def verify_action_precedence() -> None:
    """Verify REJECT > REVIEW > IGNORE > ACCEPT precedence."""

    candidate = create_candidate()

    accept_only = AdmissionDecision(
        candidate=candidate,
        evaluations=(
            create_evaluation(
                policy_id="accept",
                priority=10,
                action=AdmissionAction.ACCEPT,
            ),
        ),
    )

    ignore_over_accept = AdmissionDecision(
        candidate=candidate,
        evaluations=(
            create_evaluation(
                policy_id="accept",
                priority=10,
                action=AdmissionAction.ACCEPT,
            ),
            create_evaluation(
                policy_id="ignore",
                priority=20,
                action=AdmissionAction.IGNORE,
            ),
        ),
    )

    review_over_ignore = AdmissionDecision(
        candidate=candidate,
        evaluations=(
            create_evaluation(
                policy_id="ignore",
                priority=10,
                action=AdmissionAction.IGNORE,
            ),
            create_evaluation(
                policy_id="review",
                priority=20,
                action=AdmissionAction.REVIEW,
            ),
        ),
    )

    reject_over_everything = AdmissionDecision(
        candidate=candidate,
        evaluations=(
            create_evaluation(
                policy_id="accept",
                priority=10,
                action=AdmissionAction.ACCEPT,
            ),
            create_evaluation(
                policy_id="ignore",
                priority=20,
                action=AdmissionAction.IGNORE,
            ),
            create_evaluation(
                policy_id="review",
                priority=30,
                action=AdmissionAction.REVIEW,
            ),
            create_evaluation(
                policy_id="reject",
                priority=40,
                action=AdmissionAction.REJECT,
            ),
        ),
    )

    assert accept_only.action is AdmissionAction.ACCEPT

    assert ignore_over_accept.action is AdmissionAction.IGNORE
    assert ignore_over_accept.ignored is True
    assert ignore_over_accept.terminal is True

    assert review_over_ignore.action is AdmissionAction.REVIEW
    assert review_over_ignore.requires_review is True
    assert review_over_ignore.terminal is False

    assert reject_over_everything.action is AdmissionAction.REJECT
    assert reject_over_everything.rejected is True
    assert reject_over_everything.terminal is True

    print("[PASS] AdmissionDecision action precedence")
    print("[PASS] AdmissionDecision terminal semantics")


def verify_decision_determinism() -> None:
    """Verify equivalent unordered inputs produce equal decisions."""

    candidate = create_candidate(
        filename="deterministic.pdf",
        extension=".pdf",
        content=b"deterministic admission fixture",
    )

    duplicate = create_evaluation(
        policy_id="exact_duplicate",
        priority=10,
        action=AdmissionAction.ACCEPT,
    )

    extension = create_evaluation(
        policy_id="extension",
        priority=20,
        action=AdmissionAction.ACCEPT,
    )

    size = create_evaluation(
        policy_id="size",
        priority=30,
        action=AdmissionAction.ACCEPT,
    )

    classification = create_evaluation(
        policy_id="classification",
        priority=40,
        action=AdmissionAction.ACCEPT,
    )

    first = AdmissionDecision(
        candidate=candidate,
        evaluations=(
            classification,
            duplicate,
            size,
            extension,
        ),
    )

    second = AdmissionDecision(
        candidate=candidate,
        evaluations=(
            extension,
            size,
            duplicate,
            classification,
        ),
    )

    assert first == second
    assert first.to_dict() == second.to_dict()
    assert first.fingerprint == second.fingerprint

    print("[PASS] AdmissionDecision reproducibility")
    print("[PASS] AdmissionDecision stable fingerprint")


def verify_empty_decision_rejected() -> None:
    """Verify decisions require at least one policy evaluation."""

    try:
        AdmissionDecision(
            candidate=create_candidate(),
            evaluations=(),
        )
    except ValueError as exc:
        assert "At least one" in str(exc)
    else:
        raise AssertionError(
            "AdmissionDecision accepted an empty evaluation set"
        )

    print("[PASS] Empty admission decisions are rejected")


def main() -> None:
    verify_admission_action_contract()
    verify_context_contract()
    verify_policy_evaluation_contract()
    verify_accept_decision()
    verify_action_precedence()
    verify_decision_determinism()
    verify_empty_decision_rejected()

    print("----------------------------------------------------------------------")
    print("[PASS] All admission-model contracts verified")


if __name__ == "__main__":
    main()
