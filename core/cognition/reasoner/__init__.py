"""Genesis IV-A5 Executive Reasoner public API."""

from .contracts import ExecutiveReasoner, ReasoningRepository
from .engine import DeterministicExecutiveReasoner
from .enums import (
    ReasoningDisposition,
    ReasoningRepositoryDisposition,
    ReasoningStatus,
)
from .errors import (
    ExecutiveReasoningError,
    InvalidReasoningInputError,
    InvalidReasoningResultError,
    ReasoningRepositoryClosedError,
    ReasoningResultNotFoundError,
)
from .models import (
    ExecutiveReasoningResult,
    HypothesisRanking,
    ReasoningPolicy,
    ReasoningQuery,
    derive_reasoning_identity,
)
from .repository import InMemoryReasoningRepository
from .service import ExecutiveReasoningService

__all__ = [
    "DeterministicExecutiveReasoner",
    "ExecutiveReasoner",
    "ExecutiveReasoningError",
    "ExecutiveReasoningResult",
    "ExecutiveReasoningService",
    "HypothesisRanking",
    "InMemoryReasoningRepository",
    "InvalidReasoningInputError",
    "InvalidReasoningResultError",
    "ReasoningDisposition",
    "ReasoningPolicy",
    "ReasoningQuery",
    "ReasoningRepository",
    "ReasoningRepositoryClosedError",
    "ReasoningRepositoryDisposition",
    "ReasoningResultNotFoundError",
    "ReasoningStatus",
    "derive_reasoning_identity",
]
