"""Genesis IV-A4 Executive Evidence Correlation Engine public API."""

from .contracts import AssessmentRepository, EvidenceCorrelator
from .correlator import ExecutiveEvidenceCorrelator
from .enums import (
    AssessmentDisposition,
    AssessmentStatus,
    EvidencePolarity,
    EvidenceStrength,
)
from .errors import (
    AssessmentNotFoundError,
    AssessmentRepositoryClosedError,
    EvidenceCorrelationError,
    HypothesisCompatibilityError,
    InvalidAssessmentError,
    InvalidEvidenceLinkError,
    SituationCompatibilityError,
)
from .models import (
    AssessmentQuery,
    EvidenceLink,
    HypothesisAssessment,
    derive_assessment_identity,
)
from .repository import InMemoryAssessmentRepository
from .service import ExecutiveEvidenceService

__all__ = [
    "AssessmentDisposition",
    "AssessmentNotFoundError",
    "AssessmentQuery",
    "AssessmentRepository",
    "AssessmentRepositoryClosedError",
    "AssessmentStatus",
    "EvidenceCorrelator",
    "EvidenceCorrelationError",
    "EvidenceLink",
    "EvidencePolarity",
    "EvidenceStrength",
    "ExecutiveEvidenceCorrelator",
    "ExecutiveEvidenceService",
    "HypothesisAssessment",
    "HypothesisCompatibilityError",
    "InMemoryAssessmentRepository",
    "InvalidAssessmentError",
    "InvalidEvidenceLinkError",
    "SituationCompatibilityError",
    "derive_assessment_identity",
]
