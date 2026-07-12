"""
Shared services for controlled JARVIS knowledge assimilation.

Handlers and transitional runners use these services rather than implementing
attempt journaling, database persistence, and state transitions directly.
"""

from knowledge_engine.assimilation.services.attempts import (
    AttemptJournalService,
    AttemptStartResult,
    AttemptUpdateResult,
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
    "StateTransitionResult",
]
