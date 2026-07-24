"""
Genesis IV-R2 Observation Engine public layer API.
"""

from __future__ import annotations

from .conflicts import ConflictReport, ObservationConflictDetector
from .director import ObservationDirector
from .duplicates import DuplicateReport, ObservationDuplicateDetector
from .enums import (
    ObservationLifecycleState,
    ObservationRelationType,
    ObservationSourceMode,
)
from .errors import (
    DuplicateObservationError,
    InvalidLifecycleTransitionError,
    ObservationConflictError,
    ObservationEngineError,
    ObservationNotFoundError,
    ObservationValidationError,
)
from .factory import ObservationFactory
from .lifecycle import ObservationLifecycleManager
from .merge import MergeResult, ObservationMergeEngine
from .models import (
    ObservationInput,
    ObservationRecord,
    ObservationRelation,
    ObservationValidationIssue,
    ObservationValidationResult,
)
from .normalization import ObservationNormalizer
from .query import ObservationQuery
from .registry import ObservationRegistry
from .relationships import ObservationRelationshipManager
from .validation import ObservationValidationPolicy, ObservationValidator

__all__ = (
    "ConflictReport",
    "DuplicateObservationError",
    "DuplicateReport",
    "InvalidLifecycleTransitionError",
    "MergeResult",
    "ObservationConflictDetector",
    "ObservationConflictError",
    "ObservationDirector",
    "ObservationDuplicateDetector",
    "ObservationEngineError",
    "ObservationFactory",
    "ObservationInput",
    "ObservationLifecycleManager",
    "ObservationLifecycleState",
    "ObservationMergeEngine",
    "ObservationNormalizer",
    "ObservationNotFoundError",
    "ObservationQuery",
    "ObservationRecord",
    "ObservationRegistry",
    "ObservationRelation",
    "ObservationRelationshipManager",
    "ObservationRelationType",
    "ObservationSourceMode",
    "ObservationValidationError",
    "ObservationValidationIssue",
    "ObservationValidationPolicy",
    "ObservationValidationResult",
    "ObservationValidator",
)
