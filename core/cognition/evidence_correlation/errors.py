"""Errors for Genesis IV-A4 Executive Evidence Correlation Engine."""

from __future__ import annotations


class EvidenceCorrelationError(Exception):
    """Base error for evidence-correlation operations."""


class InvalidEvidenceLinkError(EvidenceCorrelationError, ValueError):
    """Raised when an evidence link violates the canonical contract."""


class InvalidAssessmentError(EvidenceCorrelationError, ValueError):
    """Raised when an assessment violates the canonical contract."""


class AssessmentNotFoundError(EvidenceCorrelationError, LookupError):
    """Raised when a requested assessment does not exist."""


class AssessmentRepositoryClosedError(EvidenceCorrelationError):
    """Raised when a closed assessment repository is accessed."""


class HypothesisCompatibilityError(EvidenceCorrelationError, TypeError):
    """Raised when an input is not a Genesis IV-A3 hypothesis."""


class SituationCompatibilityError(EvidenceCorrelationError, TypeError):
    """Raised when an input is not a Genesis IV-A2 situation."""
