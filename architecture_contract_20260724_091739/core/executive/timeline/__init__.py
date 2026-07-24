"""Public Genesis VI-A6.7 API."""
from .adapters import lifecycle_event_to_draft
from .contracts import (
    GENESIS_FINGERPRINT, InvalidTimelineEventError, TimelineContext,
    TimelineError, TimelineEvent, TimelineEventDraft, TimelineEventKind,
    TimelineIntegrityReport, TimelineSubsystem,
)
from .engine import ExecutiveTimelineEngine
from .queries import TimelineQuery, execute_query

__all__ = [
    "TimelineRepositoryStorageError",
    "TimelineRepositoryStatistics",
    "TimelineRepositoryIntegrityReport",
    "TimelineRepositoryIntegrityError",
    "TimelineRepositoryIndexes",
    "TimelineRepositoryError",
    "TimelineRepositoryConflictError",
    "TimelineEventSerializer",
    "TIMELINE_REPOSITORY_SCHEMA_VERSION",
    "TIMELINE_REPOSITORY_SCHEMA",
    "RepositoryIntegrityStatus",
    "ExecutiveTimelineRepository",
    "AppendOnlyTimelineStorage",
    "ExecutiveTimelineEngine", "GENESIS_FINGERPRINT",
    "InvalidTimelineEventError", "TimelineContext", "TimelineError",
    "TimelineEvent", "TimelineEventDraft", "TimelineEventKind",
    "TimelineIntegrityReport", "TimelineQuery", "TimelineSubsystem",
    "execute_query", "lifecycle_event_to_draft",
]

# BEGIN GENESIS VI-A6.8 PART A EXPORTS
from .indexes import TimelineRepositoryIndexes
from .repository import ExecutiveTimelineRepository
from .repository_contracts import (
    RepositoryIntegrityStatus,
    TIMELINE_REPOSITORY_SCHEMA,
    TIMELINE_REPOSITORY_SCHEMA_VERSION,
    TimelineRepositoryConflictError,
    TimelineRepositoryError,
    TimelineRepositoryIntegrityError,
    TimelineRepositoryIntegrityReport,
    TimelineRepositoryStatistics,
    TimelineRepositoryStorageError,
)
from .serializers import TimelineEventSerializer
from .storage import AppendOnlyTimelineStorage
# END GENESIS VI-A6.8 PART A EXPORTS

# BEGIN GENESIS VI-A6.8 PART B PUBLIC API
from .query_engine import (
    InvalidQueryError,
    RepositoryAccessError,
    TimelinePage,
    TimelineQueryEngine,
    TimelineQueryError,
    TimelineStatistics,
    canonical_event_fingerprint,
)
from .replay_readiness import (
    ReplayReadinessFinding,
    ReplayReadinessReport,
    assess_replay_readiness,
)
# END GENESIS VI-A6.8 PART B PUBLIC API
