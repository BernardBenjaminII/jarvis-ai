"""
Canonical JARVIS acquisition-admission policies.

Each policy evaluates exactly one concern and has no side effects.
"""

from knowledge_engine.acquisition.admission.policies.base import (
    AdmissionPolicy,
)
from knowledge_engine.acquisition.admission.policies.classification import (
    ClassificationAdmissionPolicy,
)
from knowledge_engine.acquisition.admission.policies.duplicate import (
    ExactDuplicatePolicy,
)
from knowledge_engine.acquisition.admission.policies.extension import (
    ExtensionAdmissionPolicy,
)
from knowledge_engine.acquisition.admission.policies.size import (
    SizeAdmissionPolicy,
)

__all__ = [
    "AdmissionPolicy",
    "ClassificationAdmissionPolicy",
    "ExactDuplicatePolicy",
    "ExtensionAdmissionPolicy",
    "SizeAdmissionPolicy",
]
