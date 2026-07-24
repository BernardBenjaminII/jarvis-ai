"""
Focused verification for the AdmissionDirector.

The Director orchestrates:

- ordered registry execution
- policy evaluation
- deterministic decision generation
- action precedence

No filesystem, database, queue, provider, or network access occurs.
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


def verify_standard_document():

    director = build_default_admission_director()

    decision = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    assert decision.accepted
    assert decision.action is AdmissionAction.ACCEPT

    print("[PASS] Standard document acceptance")


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

    print("[PASS] Duplicate document ignore")


def verify_extension_rejection():

    director = build_default_admission_director()

    decision = director.evaluate_candidate(
        candidate=make_candidate(
            filename="malware.exe",
            extension=".exe",
        ),
        context=make_context(),
    )

    assert decision.rejected
    assert decision.action is AdmissionAction.REJECT

    print("[PASS] Extension rejection")


def verify_large_document():

    director = build_default_admission_director()

    candidate = make_candidate(
        content=b"x" * (120 * 1024 * 1024),
    )

    decision = director.evaluate_candidate(
        candidate=candidate,
        context=make_context(),
    )

    assert decision.requires_review
    assert decision.action is AdmissionAction.REVIEW

    print("[PASS] Oversized review")


def verify_policy_execution_order():

    director = build_default_admission_director()

    decision = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    ordered = tuple(
        evaluation.policy_id
        for evaluation in decision.evaluations
    )

    assert ordered == (
        "exact_duplicate",
        "extension",
        "size",
        "classification",
    )

    print("[PASS] Deterministic execution order")


def verify_reproducibility():

    director = build_default_admission_director()

    first = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    second = director.evaluate_candidate(
        candidate=make_candidate(),
        context=make_context(),
    )

    assert first == second
    assert first.fingerprint == second.fingerprint

    print("[PASS] Reproducible decisions")


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

    #
    # REJECT outranks IGNORE.
    #

    assert decision.action is AdmissionAction.REJECT
    assert decision.rejected

    print("[PASS] Action precedence")


def main():

    verify_standard_document()

    verify_duplicate_document()

    verify_extension_rejection()

    verify_large_document()

    verify_policy_execution_order()

    verify_reproducibility()

    verify_action_precedence()

    print("------------------------------------------------------------")

    print("[PASS] Admission Director verified")


if __name__ == "__main__":

    main()
