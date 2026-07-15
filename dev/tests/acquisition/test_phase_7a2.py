"""
Phase VII-A2

Admission subsystem verification.

This verifies the production admission subsystem as one integrated
component.
"""

from __future__ import annotations

from dev.tests.acquisition.fixtures import (
    make_candidate,
    make_context,
)

from knowledge_engine.acquisition.admission import (
    AdmissionAction,
    build_default_admission_director,
)


def verify_default_registry():

    director = build_default_admission_director()

    registry = director.registry

    assert registry.policy_ids() == (
        "exact_duplicate",
        "extension",
        "size",
        "classification",
    )

    print("[PASS] Default policy registry")


def verify_standard_document():

    director = build_default_admission_director()

    decision = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    assert decision.accepted

    assert decision.action is AdmissionAction.ACCEPT

    print("[PASS] Standard document admission")


def verify_duplicate_document():

    director = build_default_admission_director()

    candidate = make_candidate()

    decision = director.evaluate_candidate(
        candidate=candidate,
        context=make_context(
            known_checksums={
                candidate.checksum_sha256,
            },
        ),
    )

    assert decision.ignored

    assert decision.action is AdmissionAction.IGNORE

    print("[PASS] Duplicate detection")


def verify_extension_rejection():

    director = build_default_admission_director()

    decision = director.evaluate_candidate(
        candidate=make_candidate(
            filename="virus.exe",
            extension=".exe",
        ),
        context=make_context(),
    )

    assert decision.rejected

    print("[PASS] Executable rejection")


def verify_review_path():

    director = build_default_admission_director()

    candidate = make_candidate(
        content=b"x" * (120 * 1024 * 1024),
    )

    decision = director.evaluate_candidate(
        candidate=candidate,
        context=make_context(),
    )

    assert decision.requires_review

    print("[PASS] Oversized review")


def verify_ordering():

    director = build_default_admission_director()

    decision = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
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

    print("[PASS] Deterministic ordering")


def verify_fingerprint():

    director = build_default_admission_director()

    first = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    second = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    assert first.fingerprint == second.fingerprint

    print("[PASS] Stable fingerprint")


def verify_action_precedence():

    director = build_default_admission_director()

    candidate = make_candidate(
        filename="virus.exe",
        extension=".exe",
    )

    decision = director.evaluate_candidate(
        candidate=candidate,
        context=make_context(
            known_checksums={
                candidate.checksum_sha256,
            },
        ),
    )

    assert decision.action is AdmissionAction.REJECT

    print("[PASS] Action precedence")


def main():

    verify_default_registry()

    verify_standard_document()

    verify_duplicate_document()

    verify_extension_rejection()

    verify_review_path()

    verify_ordering()

    verify_fingerprint()

    verify_action_precedence()

    print("------------------------------------------------------------")

    print("[PASS] Phase VII-A2 Admission subsystem verified")


if __name__ == "__main__":
    main()
