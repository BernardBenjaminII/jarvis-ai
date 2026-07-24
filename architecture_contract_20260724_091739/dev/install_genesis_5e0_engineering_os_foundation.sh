#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

mkdir -p core/engineering docs/constitution docs/engineering tests dev/verification

cat > core/engineering/enums.py <<'PYEOF'
from __future__ import annotations
from enum import Enum

class StableStringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

class ChangeKind(StableStringEnum):
    FEATURE = "feature"
    CERTIFICATION = "certification"
    EVOLUTION = "evolution"
    REPAIR = "repair"
    MIGRATION = "migration"
    RETIREMENT = "retirement"

class ChangeRisk(StableStringEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class DecisionStatus(StableStringEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    BLOCKED = "blocked"

class EvidenceStatus(StableStringEnum):
    ABSENT = "absent"
    PARTIAL = "partial"
    SUFFICIENT = "sufficient"
    CONTRADICTORY = "contradictory"

class GateStatus(StableStringEnum):
    NOT_EVALUATED = "not_evaluated"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"

class VerificationKind(StableStringEnum):
    UNIT = "unit"
    INTEGRATION = "integration"
    REGRESSION = "regression"
    ARCHITECTURE = "architecture"
    DETERMINISM = "determinism"
    PERFORMANCE = "performance"
    SECURITY = "security"
    RELEASE = "release"

__all__ = [
    "ChangeKind", "ChangeRisk", "DecisionStatus", "EvidenceStatus",
    "GateStatus", "StableStringEnum", "VerificationKind",
]
PYEOF

cat > core/engineering/errors.py <<'PYEOF'
class EngineeringError(Exception):
    pass

class EngineeringValidationError(EngineeringError):
    pass

class EngineeringGovernanceError(EngineeringError):
    pass

class EngineeringEvidenceError(EngineeringError):
    pass

__all__ = [
    "EngineeringError", "EngineeringEvidenceError",
    "EngineeringGovernanceError", "EngineeringValidationError",
]
PYEOF

cat > core/engineering/contracts.py <<'PYEOF'
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from core.architecture import architecture_fingerprint, canonical_json
from .enums import (
    ChangeKind, ChangeRisk, DecisionStatus, EvidenceStatus,
    GateStatus, VerificationKind,
)
from .errors import EngineeringValidationError

def _text(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise EngineeringValidationError(f"{name} must not be empty")
    return value

def _items(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))

def _mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return MappingProxyType(dict(sorted((value or {}).items())))

@dataclass(frozen=True, slots=True)
class EngineeringContract:
    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)

@dataclass(frozen=True, slots=True)
class EngineeringPrinciple(EngineeringContract):
    principle_id: str
    title: str
    statement: str
    rationale: str
    mandatory: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "principle_id", _text(self.principle_id, "principle_id"))
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "statement", _text(self.statement, "statement"))
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale"))

@dataclass(frozen=True, slots=True)
class ChangeProposal(EngineeringContract):
    change_id: str
    title: str
    kind: ChangeKind
    risk: ChangeRisk
    purpose: str
    affected_subsystems: tuple[str, ...]
    owners: tuple[str, ...]
    affected_public_apis: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()
    rollback_strategy: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "change_id", _text(self.change_id, "change_id"))
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "purpose", _text(self.purpose, "purpose"))
        object.__setattr__(self, "affected_subsystems", _items(self.affected_subsystems))
        object.__setattr__(self, "owners", _items(self.owners))
        object.__setattr__(self, "affected_public_apis", _items(self.affected_public_apis))
        object.__setattr__(self, "verification_requirements", _items(self.verification_requirements))
        object.__setattr__(self, "metadata", _mapping(self.metadata))
        if not self.affected_subsystems:
            raise EngineeringValidationError("affected_subsystems must not be empty")
        if not self.owners:
            raise EngineeringValidationError("owners must not be empty")
        if self.risk in {ChangeRisk.HIGH, ChangeRisk.CRITICAL} and not self.rollback_strategy:
            raise EngineeringValidationError("high-risk changes require rollback_strategy")

@dataclass(frozen=True, slots=True)
class VerificationEvidence(EngineeringContract):
    evidence_id: str
    change_id: str
    kind: VerificationKind
    status: EvidenceStatus
    verifier: str
    command: str
    checks_passed: int
    checks_failed: int
    artifacts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "change_id", _text(self.change_id, "change_id"))
        object.__setattr__(self, "verifier", _text(self.verifier, "verifier"))
        object.__setattr__(self, "command", _text(self.command, "command"))
        object.__setattr__(self, "artifacts", _items(self.artifacts))
        if self.checks_passed < 0 or self.checks_failed < 0:
            raise EngineeringValidationError("check counts must be non-negative")
        if self.status is EvidenceStatus.SUFFICIENT and self.checks_failed:
            raise EngineeringValidationError("sufficient evidence cannot contain failures")

@dataclass(frozen=True, slots=True)
class EngineeringGate(EngineeringContract):
    gate_id: str
    name: str
    status: GateStatus
    required_evidence_kinds: tuple[VerificationKind, ...]
    evidence_ids: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", _text(self.gate_id, "gate_id"))
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "required_evidence_kinds", tuple(sorted(set(self.required_evidence_kinds), key=lambda x: x.value)))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids))
        object.__setattr__(self, "blockers", _items(self.blockers))
        if self.status is GateStatus.PASSED and self.blockers:
            raise EngineeringValidationError("passed gate cannot contain blockers")
        if self.status is GateStatus.FAILED and not self.blockers:
            raise EngineeringValidationError("failed gate must identify blockers")

@dataclass(frozen=True, slots=True)
class GovernanceDecision(EngineeringContract):
    decision_id: str
    change_id: str
    status: DecisionStatus
    authority: str
    rationale: str
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _text(self.decision_id, "decision_id"))
        object.__setattr__(self, "change_id", _text(self.change_id, "change_id"))
        object.__setattr__(self, "authority", _text(self.authority, "authority"))
        object.__setattr__(self, "rationale", _text(self.rationale, "rationale"))
        object.__setattr__(self, "evidence_ids", _items(self.evidence_ids))
        if self.status is DecisionStatus.APPROVED and not self.evidence_ids:
            raise EngineeringValidationError("approved decision requires evidence")

@dataclass(frozen=True, slots=True)
class EngineeringAssessment(EngineeringContract):
    assessment_id: str
    proposal: ChangeProposal
    evidence: tuple[VerificationEvidence, ...]
    gates: tuple[EngineeringGate, ...]
    decision: GovernanceDecision | None = None
    explainability_improvements: tuple[str, ...] = ()
    remaining_uncertainties: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "assessment_id", _text(self.assessment_id, "assessment_id"))
        object.__setattr__(self, "evidence", tuple(sorted(self.evidence, key=lambda x: x.evidence_id)))
        object.__setattr__(self, "gates", tuple(sorted(self.gates, key=lambda x: x.gate_id)))
        object.__setattr__(self, "explainability_improvements", _items(self.explainability_improvements))
        object.__setattr__(self, "remaining_uncertainties", _items(self.remaining_uncertainties))
        known = {item.evidence_id for item in self.evidence}
        if self.decision:
            missing = set(self.decision.evidence_ids) - known
            if missing:
                raise EngineeringValidationError(f"unknown evidence IDs: {sorted(missing)}")

__all__ = [
    "ChangeProposal", "EngineeringAssessment", "EngineeringContract",
    "EngineeringGate", "EngineeringPrinciple", "GovernanceDecision",
    "VerificationEvidence",
]
PYEOF

cat > core/engineering/constitution.py <<'PYEOF'
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
PYEOF

cat > core/engineering/__init__.py <<'PYEOF'
from .constitution import ENGINEERING_CONSTITUTION, constitution_fingerprint
from .contracts import (
    ChangeProposal, EngineeringAssessment, EngineeringContract,
    EngineeringGate, EngineeringPrinciple, GovernanceDecision,
    VerificationEvidence,
)
from .enums import (
    ChangeKind, ChangeRisk, DecisionStatus, EvidenceStatus,
    GateStatus, StableStringEnum, VerificationKind,
)
from .errors import (
    EngineeringError, EngineeringEvidenceError,
    EngineeringGovernanceError, EngineeringValidationError,
)

__all__ = [
    "ENGINEERING_CONSTITUTION", "ChangeKind", "ChangeProposal", "ChangeRisk",
    "DecisionStatus", "EngineeringAssessment", "EngineeringContract",
    "EngineeringError", "EngineeringEvidenceError", "EngineeringGate",
    "EngineeringGovernanceError", "EngineeringPrinciple",
    "EngineeringValidationError", "EvidenceStatus", "GateStatus",
    "GovernanceDecision", "StableStringEnum", "VerificationEvidence",
    "VerificationKind", "constitution_fingerprint",
]
PYEOF

cat > docs/constitution/ENGINEERING_CONSTITUTION.md <<'EOF'
# JARVIS Engineering Constitution

**Status:** Foundational  
**Authority:** Commander-approved engineering doctrine  
**Scope:** All code, tooling, documentation, migrations, certifications, and releases

## Preamble

The Engineering Operating System ensures that implementation does not outrun
understanding, automation does not outrun authority, and growth does not create
hidden architectural uncertainty.

## Principles

1. **Explicit Ownership:** Every concept and public contract has one canonical owner.
2. **Contract Before Implementation:** Stable boundaries are explicit before runtime dependence.
3. **Deterministic Evidence:** Equivalent state produces equivalent analysis and fingerprints.
4. **Verification Is Architecture:** A capability is incomplete until behavior, boundaries, and regressions are verified.
5. **Compatibility Is Explicit:** Certified APIs remain compatible unless an approved breaking change exists.
6. **Explainability Must Increase:** Every architectural change leaves the repository more explainable than before.
7. **Human Authority:** Deletion, breaking migration, and release approval require explicit human authority.
8. **Deletion Requires Evidence:** Ownership, dependencies, compatibility, migration, and regressions must support removal.
9. **Least Authority:** Read-only intelligence remains separate from source-changing automation.

## Change Classes

- Feature Pack
- Certification Pack
- Evolution Pack
- Repair Pack
- Migration Pack
- Retirement Pack

## Development Lifecycle

```text
Need
  ↓
Architecture
  ↓
Ownership
  ↓
Contracts
  ↓
Implementation
  ↓
Verification
  ↓
Certification
  ↓
Evolution Plan
  ↓
Commit
  ↓
Release
```

## Required Questions

Every material change must answer:

1. Who owns the concept?
2. Which contracts define it?
3. Which public APIs may change?
4. How is compatibility preserved or migrated?
5. How is the change verified?
6. What is the rollback strategy?
7. What uncertainty remains?
8. How does explainability improve?

## Governing Maxim

> Every architectural change must leave the repository more explainable than before it began.
EOF

cat > docs/engineering/engineering_os_architecture.md <<'EOF'
# Engineering Operating System Architecture

**Pack:** Genesis V-E0  
**Status:** Foundation

The Engineering OS governs how JARVIS is designed, verified, certified,
evolved, migrated, and released.

```text
Engineering OS
├── Constitution
├── Architecture Intelligence
├── Verification
├── Certification
├── Compatibility Governance
├── Evolution Planning
├── Release Readiness
└── Drift Detection
```

Architecture Intelligence describes repository reality. The Engineering OS
evaluates proposed change against engineering doctrine and authority.

Genesis V-E0 introduces immutable, deterministic contracts for principles,
change proposals, verification evidence, engineering gates, governance
decisions, and complete assessments.

This foundation performs no scanning, Git writes, source modification, network
access, runtime orchestration, or autonomous approval.

The next pack is Genesis V-E1: Public API Compatibility Restoration.
EOF

cat > tests/test_genesis_5e0_engineering_os_foundation.py <<'PYEOF'
from __future__ import annotations
import unittest

from core.engineering import (
    ENGINEERING_CONSTITUTION, ChangeKind, ChangeProposal, ChangeRisk,
    DecisionStatus, EngineeringAssessment, EngineeringGate,
    EngineeringValidationError, EvidenceStatus, GateStatus,
    GovernanceDecision, VerificationEvidence, VerificationKind,
    constitution_fingerprint,
)

class EngineeringOSFoundationTests(unittest.TestCase):
    def test_constitution_unique_and_deterministic(self):
        ids = [item.principle_id for item in ENGINEERING_CONSTITUTION]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(constitution_fingerprint(), constitution_fingerprint())
        self.assertEqual(len(constitution_fingerprint()), 64)

    def test_proposal_is_immutable(self):
        item = ChangeProposal(
            "v-e0", "Foundation", ChangeKind.FEATURE, ChangeRisk.LOW,
            "Establish governance.", ("engineering",), ("core.engineering",),
        )
        with self.assertRaises((AttributeError, TypeError)):
            item.title = "Changed"

    def test_proposal_requires_owner(self):
        with self.assertRaises(EngineeringValidationError):
            ChangeProposal(
                "bad", "Bad", ChangeKind.FEATURE, ChangeRisk.LOW,
                "Fixture.", ("engineering",), (),
            )

    def test_high_risk_requires_rollback(self):
        with self.assertRaises(EngineeringValidationError):
            ChangeProposal(
                "risk", "Risk", ChangeKind.MIGRATION, ChangeRisk.HIGH,
                "Fixture.", ("reasoning",), ("core.reasoning",),
            )

    def test_sufficient_evidence_cannot_fail(self):
        with self.assertRaises(EngineeringValidationError):
            VerificationEvidence(
                "ev", "change", VerificationKind.REGRESSION,
                EvidenceStatus.SUFFICIENT, "verify.sh", "./verify.sh", 5, 1,
            )

    def test_failed_gate_requires_blocker(self):
        with self.assertRaises(EngineeringValidationError):
            EngineeringGate(
                "gate", "Gate", GateStatus.FAILED,
                (VerificationKind.REGRESSION,),
            )

    def test_approved_decision_requires_evidence(self):
        with self.assertRaises(EngineeringValidationError):
            GovernanceDecision(
                "decision", "change", DecisionStatus.APPROVED,
                "Commander", "Approved.",
            )

    def test_complete_assessment(self):
        proposal = ChangeProposal(
            "v-e0", "Foundation", ChangeKind.FEATURE, ChangeRisk.LOW,
            "Establish governance.", ("architecture", "engineering"),
            ("core.engineering",),
        )
        evidence = VerificationEvidence(
            "unit", "v-e0", VerificationKind.UNIT,
            EvidenceStatus.SUFFICIENT, "verify.sh", "./verify.sh", 8, 0,
        )
        gate = EngineeringGate(
            "foundation", "Foundation", GateStatus.PASSED,
            (VerificationKind.UNIT,), ("unit",),
        )
        decision = GovernanceDecision(
            "approve", "v-e0", DecisionStatus.APPROVED,
            "Commander", "Accepted.", ("unit",),
        )
        assessment = EngineeringAssessment(
            "assessment", proposal, (evidence,), (gate,), decision,
            ("Governance is explicit.",),
        )
        self.assertEqual(len(assessment.fingerprint()), 64)

    def test_unknown_decision_evidence_rejected(self):
        proposal = ChangeProposal(
            "change", "Change", ChangeKind.FEATURE, ChangeRisk.LOW,
            "Fixture.", ("engineering",), ("core.engineering",),
        )
        decision = GovernanceDecision(
            "decision", "change", DecisionStatus.APPROVED,
            "Commander", "Fixture.", ("missing",),
        )
        with self.assertRaises(EngineeringValidationError):
            EngineeringAssessment("assessment", proposal, (), (), decision)

if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_5e0_engineering_os_foundation.py <<'PYEOF'
#!/usr/bin/env python3
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1

def main() -> int:
    failures = 0
    required = (
        ROOT / "core/engineering/__init__.py",
        ROOT / "core/engineering/constitution.py",
        ROOT / "core/engineering/contracts.py",
        ROOT / "core/engineering/enums.py",
        ROOT / "core/engineering/errors.py",
        ROOT / "docs/constitution/ENGINEERING_CONSTITUTION.md",
        ROOT / "docs/engineering/engineering_os_architecture.md",
        ROOT / "tests/test_genesis_5e0_engineering_os_foundation.py",
    )
    failures += check(all(path.is_file() for path in required), "Required Engineering OS files")

    result = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", "core/engineering",
         "tests/test_genesis_5e0_engineering_os_foundation.py"],
        cwd=ROOT, check=False,
    )
    failures += check(result.returncode == 0, "Engineering OS compilation")

    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "core/engineering").glob("*.py")
    )
    failures += check("@dataclass(frozen=True, slots=True)" in source, "Immutable contracts")
    failures += check(
        "subprocess" not in source and "requests" not in source and "os.system" not in source,
        "No process, network, or source-write side effects",
    )
    failures += check(
        "from core.architecture import" in source,
        "Architecture Intelligence integration",
    )

    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "-v",
         "tests.test_genesis_5e0_engineering_os_foundation"],
        cwd=ROOT, check=False,
    )
    failures += check(tests.returncode == 0, "Genesis V-E0 unit tests")

    smoke = (
        "from core.engineering import ENGINEERING_CONSTITUTION, constitution_fingerprint;"
        "a=constitution_fingerprint();b=constitution_fingerprint();"
        "assert a==b and len(a)==64 and len(ENGINEERING_CONSTITUTION)>=9;print(a)"
    )
    one = subprocess.run([sys.executable, "-c", smoke], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    two = subprocess.run([sys.executable, "-c", smoke], cwd=ROOT, check=False,
                         capture_output=True, text=True)
    failures += check(
        one.returncode == 0 and two.returncode == 0 and one.stdout == two.stdout,
        "Deterministic Engineering Constitution fingerprint",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_5e0.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E0 — ENGINEERING OPERATING SYSTEM FOUNDATION"
echo "========================================================================"
"${PYTHON_BIN}" dev/verification/verify_genesis_5e0_engineering_os_foundation.py
SHEOF

chmod +x dev/verify_genesis_5e0.sh     dev/verification/verify_genesis_5e0_engineering_os_foundation.py

"${PYTHON_BIN}" dev/verification/verify_genesis_5e0_engineering_os_foundation.py

echo
echo "Genesis V-E0 Engineering Operating System Foundation installed."
