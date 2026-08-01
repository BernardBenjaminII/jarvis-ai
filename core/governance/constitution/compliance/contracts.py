from __future__ import annotations

from enum import Enum


COMPLIANCE_SCHEMA_VERSION = "1.0.0"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    REVIEW_REQUIRED = "review_required"
    NONCOMPLIANT = "noncompliant"
    NOT_APPLICABLE = "not_applicable"


class FindingSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


APPLICABLE_ARTICLE_STATUSES = frozenset({"ratified", "review_required"})
