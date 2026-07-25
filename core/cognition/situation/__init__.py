"""Genesis IV-A2 Executive Situation Model public API."""

from .contracts import SituationProjector, SituationRepository
from .enums import (
    SituationDisposition,
    SituationRelationType,
    SituationStatus,
)
from .errors import (
    InvalidSituationError,
    ObservationCompatibilityError,
    SituationError,
    SituationNotFoundError,
    SituationRepositoryClosedError,
)
from .models import (
    SituationQuery,
    SituationRelation,
    SituationSnapshot,
    derive_situation_confidence,
    derive_situation_identity,
    derive_situation_severity,
)
from .projector import ExecutiveSituationProjector
from .repository import InMemorySituationRepository
from .service import ExecutiveSituationService

__all__ = [
    "ExecutiveSituationProjector",
    "ExecutiveSituationService",
    "InMemorySituationRepository",
    "InvalidSituationError",
    "ObservationCompatibilityError",
    "SituationDisposition",
    "SituationError",
    "SituationNotFoundError",
    "SituationProjector",
    "SituationQuery",
    "SituationRelation",
    "SituationRelationType",
    "SituationRepository",
    "SituationRepositoryClosedError",
    "SituationSnapshot",
    "SituationStatus",
    "derive_situation_confidence",
    "derive_situation_identity",
    "derive_situation_severity",
]
