"""Genesis IV-A3 Executive Hypothesis Engine public API."""

from .contracts import HypothesisGenerator, HypothesisRepository
from .enums import (
    HypothesisDisposition,
    HypothesisKind,
    HypothesisStatus,
)
from .errors import (
    HypothesisError,
    HypothesisNotFoundError,
    HypothesisRepositoryClosedError,
    InvalidHypothesisError,
    SituationCompatibilityError,
)
from .generator import ExecutiveHypothesisGenerator
from .models import (
    Hypothesis,
    HypothesisProposal,
    HypothesisQuery,
    derive_hypothesis_identity,
)
from .repository import InMemoryHypothesisRepository
from .service import ExecutiveHypothesisService

__all__ = [
    "ExecutiveHypothesisGenerator",
    "ExecutiveHypothesisService",
    "Hypothesis",
    "HypothesisDisposition",
    "HypothesisError",
    "HypothesisGenerator",
    "HypothesisKind",
    "HypothesisNotFoundError",
    "HypothesisProposal",
    "HypothesisQuery",
    "HypothesisRepository",
    "HypothesisRepositoryClosedError",
    "HypothesisStatus",
    "InMemoryHypothesisRepository",
    "InvalidHypothesisError",
    "SituationCompatibilityError",
    "derive_hypothesis_identity",
]
