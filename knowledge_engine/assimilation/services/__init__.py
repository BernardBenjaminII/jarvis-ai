"""
Shared services for controlled JARVIS knowledge assimilation.

Handlers and transitional runners use these services rather than directly
implementing extraction, attempt journaling, persistence, or state changes.
"""

from knowledge_engine.assimilation.services.attempts import (
    AttemptJournalService,
    AttemptStartResult,
    AttemptUpdateResult,
)
from knowledge_engine.assimilation.services.extraction import (
    ExtractionResult,
    ExtractionService,
)
from knowledge_engine.assimilation.services.persistence import (
    DocumentPersistenceResult,
    DocumentPersistenceService,
)
from knowledge_engine.assimilation.services.state import (
    AssimilationStateService,
    StateTransitionResult,
)

__all__ = [
    "AssimilationStateService",
    "AttemptJournalService",
    "AttemptStartResult",
    "AttemptUpdateResult",
    "DocumentPersistenceResult",
    "DocumentPersistenceService",
    "ExtractionResult",
    "ExtractionService",
    "StateTransitionResult",
]
