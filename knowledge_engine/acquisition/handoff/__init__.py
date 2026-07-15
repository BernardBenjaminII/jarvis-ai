"""
Controlled JARVIS acquisition-to-assimilation handoff.
"""

from knowledge_engine.acquisition.handoff.identity import (
    build_assimilation_handoff_id,
)
from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffBuildResult,
    AssimilationHandoffRecord,
    AssimilationHandoffState,
)
from knowledge_engine.acquisition.handoff.repository import (
    AssimilationHandoffRepository,
)
from knowledge_engine.acquisition.handoff.schema import (
    ensure_assimilation_handoff_schema,
)
from knowledge_engine.acquisition.handoff.service import (
    AssimilationHandoffService,
)

__all__ = [
    "AssimilationHandoffBuildResult",
    "AssimilationHandoffRecord",
    "AssimilationHandoffRepository",
    "AssimilationHandoffService",
    "AssimilationHandoffState",
    "build_assimilation_handoff_id",
    "ensure_assimilation_handoff_schema",
]
