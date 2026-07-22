from __future__ import annotations
from core.architecture import architecture_fingerprint
from .contracts import EngineeringPrinciple

ENGINEERING_CONSTITUTION = (
    EngineeringPrinciple("ENG-001", "Explicit Ownership",
        "Every architectural concept and public contract has one canonical owner.",
        "Ownership prevents duplication and conflicting evolution."),
    EngineeringPrinciple("ENG-002", "Contract Before Implementation",
        "Stable boundaries are expressed as explicit contracts before runtime dependence.",
        "Contracts make integration, testing, and migration governable."),
    EngineeringPrinciple("ENG-003", "Deterministic Evidence",
        "Equivalent repository state produces equivalent engineering evidence.",
        "Certification must be reproducible."),
    EngineeringPrinciple("ENG-004", "Verification Is Architecture",
        "A capability is incomplete until behavior, boundaries, and regressions are verified.",
        "Verification preserves architectural intent."),
    EngineeringPrinciple("ENG-005", "Compatibility Is Explicit",
        "Certified public APIs remain compatible unless a breaking change is approved.",
        "Silent API drift creates cascading failures."),
    EngineeringPrinciple("ENG-006", "Explainability Must Increase",
        "Every architectural change leaves the repository more explainable than before.",
        "Long-lived systems must become easier to understand as they grow."),
    EngineeringPrinciple("ENG-007", "Human Authority",
        "Irreversible changes require explicit human authority.",
        "Architecture Intelligence advises but does not seize authority."),
    EngineeringPrinciple("ENG-008", "Deletion Requires Evidence",
        "Code is retired only after ownership, dependency, compatibility, and migration evidence.",
        "Confidence is not proof of safe removal."),
    EngineeringPrinciple("ENG-009", "Least Authority",
        "Engineering automation operates with the least authority required.",
        "Read-only analysis must remain separate from source-changing tools."),
)

def constitution_fingerprint() -> str:
    return architecture_fingerprint(ENGINEERING_CONSTITUTION)

__all__ = ["ENGINEERING_CONSTITUTION", "constitution_fingerprint"]
