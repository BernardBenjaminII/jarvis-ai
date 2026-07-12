"""
Shared services for controlled JARVIS knowledge assimilation.

Handlers and transitional runners use these services instead of implementing
catalog and queue state transitions directly.
"""

from knowledge_engine.assimilation.services.state import (
    AssimilationStateService,
    StateTransitionResult,
)

__all__ = [
    "AssimilationStateService",
    "StateTransitionResult",
]
