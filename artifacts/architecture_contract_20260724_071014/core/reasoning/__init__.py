"""Public interface for the JARVIS Reasoning Engine."""

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
from core.reasoning.generation import (
    DeterministicHypothesisGenerator,
    HypothesisGenerationResult,
)
from core.reasoning.knowledge import (
    AdaptedEvidenceBatch,
    KnowledgeEvidenceAdapter,
    KnowledgeEvidenceAdapterError,
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
from core.reasoning.pipeline import (
    KnowledgeReasoningOutcome,
    KnowledgeReasoningPipeline,
    KnowledgeSearch,
)
from core.reasoning.service import ENGINE_VERSION, ReasoningEngine

__all__ = [
    "ENGINE_VERSION",
    "AdaptedEvidenceBatch",
    "DeterministicHypothesisGenerator",
    "DuplicateReasoningElementError",
    "EvidenceItem",
    "EvidenceKind",
    "EvidenceStance",
    "Hypothesis",
    "HypothesisAssessment",
    "HypothesisDisposition",
    "HypothesisGenerationResult",
    "InvalidReasoningRequestError",
    "KnowledgeEvidenceAdapter",
    "KnowledgeEvidenceAdapterError",
    "KnowledgeReasoningOutcome",
    "KnowledgeReasoningPipeline",
    "KnowledgeSearch",
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
