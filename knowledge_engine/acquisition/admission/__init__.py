"""
JARVIS acquisition admission-policy engine.

The package evaluates discovered SourceCandidate objects and produces
immutable AdmissionDecision results.

Phase VII-A2 remains read-only.
"""

from knowledge_engine.acquisition.admission.director import (
    AdmissionDirector,
)
from knowledge_engine.acquisition.admission.models import (
    AdmissionAction,
    AdmissionContext,
    AdmissionDecision,
    PolicyEvaluation,
)
from knowledge_engine.acquisition.admission.policies import (
    AdmissionPolicy,
    ClassificationAdmissionPolicy,
    ExactDuplicatePolicy,
    ExtensionAdmissionPolicy,
    SizeAdmissionPolicy,
)
from knowledge_engine.acquisition.admission.registry import (
    AdmissionPolicyRegistry,
)


def build_default_admission_registry(
) -> AdmissionPolicyRegistry:
    """
    Construct the canonical Phase VII-A2 admission-policy registry.
    """

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

    return registry


def build_default_admission_director(
) -> AdmissionDirector:
    """
    Construct the canonical Phase VII-A2 AdmissionDirector.
    """

    return AdmissionDirector(
        build_default_admission_registry()
    )


__all__ = [
    "AdmissionAction",
    "AdmissionContext",
    "AdmissionDecision",
    "AdmissionDirector",
    "AdmissionPolicy",
    "AdmissionPolicyRegistry",
    "ClassificationAdmissionPolicy",
    "ExactDuplicatePolicy",
    "ExtensionAdmissionPolicy",
    "PolicyEvaluation",
    "SizeAdmissionPolicy",
    "build_default_admission_director",
    "build_default_admission_registry",
]
