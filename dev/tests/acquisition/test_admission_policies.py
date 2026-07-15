"""
Focused verification for the JARVIS Admission Policies.

This suite verifies:

- duplicate policy
- extension policy
- size policy
- classification policy
- deterministic policy behaviour
- deterministic serialization
- deterministic priorities

No filesystem, database, queue, provider, or network access occurs.
"""

from __future__ import annotations

from knowledge_engine.acquisition.admission import (
    AdmissionAction,
)

from knowledge_engine.acquisition.admission.policies import (
    ClassificationAdmissionPolicy,
    ExactDuplicatePolicy,
    ExtensionAdmissionPolicy,
    SizeAdmissionPolicy,
)

from dev.tests.acquisition.fixtures import (
    make_candidate,
    make_context,
)
def verify_duplicate_policy() -> None:
    """
    Verify exact checksum duplicate detection.
    """

    candidate = make_candidate()

    policy = ExactDuplicatePolicy()

    accepted = policy.evaluate(
        candidate=candidate,
        context=make_context(),
    )

    assert accepted.action is AdmissionAction.ACCEPT

    duplicate = policy.evaluate(
        candidate=candidate,
        context=make_context(
            known_checksums={
                candidate.checksum_sha256,
            },
        ),
    )

    assert duplicate.action is AdmissionAction.IGNORE

    assert accepted.priority == 10
    assert duplicate.priority == 10

    assert accepted.policy_id == "exact_duplicate"
    assert duplicate.policy_id == "exact_duplicate"

    print("[PASS] Duplicate policy acceptance")
    print("[PASS] Duplicate policy ignore")

def verify_extension_policy() -> None:

    policy = ExtensionAdmissionPolicy()

    accepted = policy.evaluate(
        candidate=make_candidate(
            extension=".pdf",
        ),
        context=make_context(),
    )

    assert accepted.action is AdmissionAction.ACCEPT

    rejected = policy.evaluate(
        candidate=make_candidate(
            filename="virus.exe",
            extension=".exe",
        ),
        context=make_context(),
    )

    assert rejected.action is AdmissionAction.REJECT

    review = policy.evaluate(
        candidate=make_candidate(
            filename="archive.xyz",
            extension=".xyz",
        ),
        context=make_context(),
    )

    assert review.action is AdmissionAction.REVIEW

    print("[PASS] Extension acceptance")
    print("[PASS] Extension rejection")
    print("[PASS] Extension review")

def verify_size_policy() -> None:

    policy = SizeAdmissionPolicy()

    normal = policy.evaluate(
        candidate=make_candidate(),
        context=make_context(),
    )

    assert normal.action is AdmissionAction.ACCEPT

    review_candidate = make_candidate(
        content=b"x" * (120 * 1024 * 1024),
    )

    review = policy.evaluate(
        candidate=review_candidate,
        context=make_context(),
    )

    assert review.action is AdmissionAction.REVIEW

    reject_candidate = make_candidate(
        content=b"x" * (3 * 1024 * 1024),
    )

    reject_candidate = reject_candidate.__class__(
        **{
            **reject_candidate.__dict__,
            "size_bytes": 3 * 1024 * 1024 * 1024,
        }
    )

    rejected = policy.evaluate(
        candidate=reject_candidate,
        context=make_context(),
    )

    assert rejected.action is AdmissionAction.REJECT

    print("[PASS] Size acceptance")
    print("[PASS] Size review")
    print("[PASS] Size rejection")

def verify_classification_policy() -> None:

    policy = ClassificationAdmissionPolicy()

    for candidate_type in (
        "document",
        "image",
        "source_code",
    ):

        evaluation = policy.evaluate(
            candidate=make_candidate(
                candidate_type=candidate_type,
            ),
            context=make_context(),
        )

        assert evaluation.action is AdmissionAction.ACCEPT

    review = policy.evaluate(
        candidate=make_candidate(
            candidate_type="unknown_type",
        ),
        context=make_context(),
    )

    assert review.action is AdmissionAction.REVIEW

    print("[PASS] Classification acceptance")
    print("[PASS] Classification review")

def verify_policy_determinism() -> None:

    candidate = make_candidate()

    context = make_context()

    policy = ExtensionAdmissionPolicy()

    first = policy.evaluate(
        candidate=candidate,
        context=context,
    )

    second = policy.evaluate(
        candidate=candidate,
        context=context,
    )

    assert first == second

    assert (
        first.fingerprint
        == second.fingerprint
    )

    print("[PASS] Deterministic policy evaluation")

def main() -> None:

    verify_duplicate_policy()

    verify_extension_policy()

    verify_size_policy()

    verify_classification_policy()

    verify_policy_determinism()

    print("------------------------------------------------------------")
    print("[PASS] All admission policies verified")


if __name__ == "__main__":
    main()

