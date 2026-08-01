from __future__ import annotations

from enum import Enum


CERTIFICATION_SCHEMA_VERSION = "1.0.0"


class ScenarioKind(str, Enum):
    POSITIVE_COMPLIANCE = "positive_compliance"
    NEGATIVE_COMPLIANCE = "negative_compliance"
    REVIEW_REQUIRED = "review_required"
    NOT_APPLICABLE = "not_applicable"
    COVERAGE = "coverage"
    RANKING = "ranking"
    TRACEABILITY = "traceability"
    DETERMINISM = "determinism"


class CertificationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIPPED = "skipped"
