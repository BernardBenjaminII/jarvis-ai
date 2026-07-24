"""Canonical public API for JARVIS cognition.

This package root intentionally exposes both:

* Genesis VI executive cognition contracts; and
* Genesis III cognitive workspace contracts.

Genesis III-A3A restores the workspace exports without replacing or
renaming any Genesis VI symbols.
"""

from .cycle import CognitionCycleController, CognitionCycleSnapshot
from .enums import (
    AttentionReason,
    CognitiveCycleStatus,
    CognitiveEventKind,
    CognitiveState,
    MemoryEntryKind,
)
from .errors import (
    AttentionAllocationError,
    CognitionCycleClosedError,
    CognitionCycleNotActiveError,
    CognitionError,
    DuplicateMemoryEntryError,
    InvalidCognitiveContextError,
    InvalidCognitiveStateError,
    InvalidStateTransitionError,
    WorkingMemoryCapacityError,
)
from .models import (
    AttentionAllocation,
    AttentionCandidate,
    CognitiveEvent,
    ExecutiveContext,
    MemoryEntry,
    StateTransition,
    freeze_mapping,
    utc_now,
)
from .session import (
    ExecutiveSession,
    ExecutiveSessionEvent,
    ExecutiveSessionSnapshot,
    ExecutiveSessionStatus,
)
from .state_machine import (
    DEFAULT_TRANSITION_POLICY,
    CognitiveStateMachine,
    StateMachineSnapshot,
    TransitionGuard,
    TransitionPolicy,
)
from .working_memory import WorkingMemory, WorkingMemorySnapshot
from .workspace import (
    Assumption,
    CognitiveWorkspace,
    CognitiveWorkspaceCatalog,
    CognitiveWorkspaceCodec,
    CognitiveWorkspaceConflictError,
    CognitiveWorkspaceError,
    CognitiveWorkspaceNotFoundError,
    CognitiveWorkspaceRepository,
    CognitiveWorkspaceRepositoryError,
    CognitiveWorkspaceService,
    EvidenceReference,
    Hypothesis,
    HypothesisStatus,
    OpenQuestion,
    SQLiteCognitiveWorkspaceRepository,
    SortDirection,
    WorkspaceCatalogEntry,
    WorkspaceEvent,
    WorkspaceEventKind,
    WorkspaceQuery,
    WorkspaceSnapshot,
    WorkspaceSortField,
    WorkspaceStatus,
)

__all__ = [
    # Genesis VI executive cognition.
    "AttentionAllocation",
    "AttentionAllocationError",
    "AttentionCandidate",
    "AttentionReason",
    "CognitionCycleClosedError",
    "CognitionCycleController",
    "CognitionCycleNotActiveError",
    "CognitionCycleSnapshot",
    "CognitiveCycleStatus",
    "CognitiveEvent",
    "CognitiveEventKind",
    "CognitiveState",
    "CognitiveStateMachine",
    "CognitionError",
    "DEFAULT_TRANSITION_POLICY",
    "DuplicateMemoryEntryError",
    "ExecutiveContext",
    "ExecutiveSession",
    "ExecutiveSessionEvent",
    "ExecutiveSessionSnapshot",
    "ExecutiveSessionStatus",
    "InvalidCognitiveContextError",
    "InvalidCognitiveStateError",
    "InvalidStateTransitionError",
    "MemoryEntry",
    "MemoryEntryKind",
    "StateMachineSnapshot",
    "StateTransition",
    "TransitionGuard",
    "TransitionPolicy",
    "WorkingMemory",
    "WorkingMemoryCapacityError",
    "WorkingMemorySnapshot",
    "freeze_mapping",
    "utc_now",
    # Genesis III cognitive workspace.
    "Assumption",
    "CognitiveWorkspace",
    "CognitiveWorkspaceCatalog",
    "CognitiveWorkspaceCodec",
    "CognitiveWorkspaceConflictError",
    "CognitiveWorkspaceError",
    "CognitiveWorkspaceNotFoundError",
    "CognitiveWorkspaceRepository",
    "CognitiveWorkspaceRepositoryError",
    "CognitiveWorkspaceService",
    "EvidenceReference",
    "Hypothesis",
    "HypothesisStatus",
    "OpenQuestion",
    "SQLiteCognitiveWorkspaceRepository",
    "SortDirection",
    "WorkspaceCatalogEntry",
    "WorkspaceEvent",
    "WorkspaceEventKind",
    "WorkspaceQuery",
    "WorkspaceSnapshot",
    "WorkspaceSortField",
    "WorkspaceStatus",
]
