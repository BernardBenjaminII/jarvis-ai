"""Public interface for the JARVIS Reasoning Engine foundation."""

from core.reasoning.enums import (
    EvidenceKind,
    EvidenceStance,
    HypothesisDisposition,
    ReasoningStatus,
)
from core.reasoning.errors import (
    DuplicateReasoningElementError,
    InvalidReasoningRequestError,
    ReasoningError,
    UnknownEvidenceReferenceError,
)
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
    PlanningRecommendation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningTraceStep,
    canonical_fingerprint,
)
from core.reasoning.service import ENGINE_VERSION, ReasoningEngine

__all__ = [
    "ENGINE_VERSION",
    "DuplicateReasoningElementError",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceStance",
    "Hypothesis",
    "HypothesisAssessment",
    "HypothesisDisposition",
    "InvalidReasoningRequestError",
    "PlanningRecommendation",
    "ReasoningEngine",
    "ReasoningError",
    "ReasoningRequest",
    "ReasoningResult",
    "ReasoningStatus",
    "ReasoningTraceStep",
    "UnknownEvidenceReferenceError",
    "canonical_fingerprint",
]
