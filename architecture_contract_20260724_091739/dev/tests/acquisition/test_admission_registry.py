"""
Focused verification for the AdmissionPolicyRegistry.
"""

from __future__ import annotations

from knowledge_engine.acquisition.admission.registry import (
    AdmissionPolicyRegistry,
)

from knowledge_engine.acquisition.admission.policies import (
    ExactDuplicatePolicy,
    ExtensionAdmissionPolicy,
    SizeAdmissionPolicy,
    ClassificationAdmissionPolicy,
)


def verify_empty_registry() -> None:

    registry = AdmissionPolicyRegistry()

    assert len(registry) == 0

    assert registry.policy_ids() == ()

    assert registry.ordered_policies() == ()

    print("[PASS] Empty registry")

def verify_registration() -> None:

    registry = AdmissionPolicyRegistry()

    registry.register(
        ExactDuplicatePolicy()
    )

    registry.register(
        ExtensionAdmissionPolicy()
    )

    registry.register(
        SizeAdmissionPolicy()
    )

    registry.register(
        ClassificationAdmissionPolicy()
    )

    assert len(registry) == 4

    assert registry.policy_ids() == (
        "exact_duplicate",
        "extension",
        "size",
        "classification",
    )

    print("[PASS] Registration")

def verify_duplicate_registration():

    registry = AdmissionPolicyRegistry()

    registry.register(
        ExactDuplicatePolicy()
    )

    try:

        registry.register(
            ExactDuplicatePolicy()
        )

    except ValueError:

        print("[PASS] Duplicate registration rejection")

        return

    raise AssertionError(
        "Duplicate registration accepted."
    )


def verify_priority_order() -> None:

    registry = AdmissionPolicyRegistry()

    registry.register(
        ClassificationAdmissionPolicy()
    )

    registry.register(
        SizeAdmissionPolicy()
    )

    registry.register(
        ExtensionAdmissionPolicy()
    )

    registry.register(
        ExactDuplicatePolicy()
    )

    ordered = tuple(
        policy.policy_id
        for policy in registry.ordered_policies()
    )

    assert ordered == (
        "exact_duplicate",
        "extension",
        "size",
        "classification",
    )

    print("[PASS] Deterministic priority ordering")

def verify_lookup():

    registry = AdmissionPolicyRegistry()

    duplicate = ExactDuplicatePolicy()

    registry.register(
        duplicate
    )

    assert (
        registry.get(
            "exact_duplicate"
        )
        is duplicate
    )

    print("[PASS] Policy lookup")


def verify_iteration_stability() -> None:

    registry = AdmissionPolicyRegistry()

    registry.register(
        ExactDuplicatePolicy()
    )

    registry.register(
        ExtensionAdmissionPolicy()
    )

    first = tuple(
        p.policy_id
        for p in registry.ordered_policies()
    )

    second = tuple(
        p.policy_id
        for p in registry.ordered_policies()
    )

    assert first == second

    print("[PASS] Stable iteration")


def main():

    verify_empty_registry()

    verify_registration()

    verify_duplicate_registration()

    verify_priority_order()

    verify_lookup()

    verify_iteration_stability()

    print("---------------------------------------------")

    print(
        "[PASS] Admission registry verified"
    )


if __name__ == "__main__":

    main()
