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
