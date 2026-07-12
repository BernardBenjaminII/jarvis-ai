"""
Shared services for controlled JARVIS knowledge assimilation.

Handlers and transitional runners use these services instead of implementing
database persistence and lifecycle transitions directly.
"""

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
    "DocumentPersistenceResult",
    "DocumentPersistenceService",
    "StateTransitionResult",
]
