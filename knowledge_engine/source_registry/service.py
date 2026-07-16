"""
Application service for JARVIS Phase VII-B2 source registry.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from knowledge_engine.acquisition_control import (
    AdmissionDecision,
    AdmissionStatus,
    NormalizedSource,
)

from .contracts import (
    RegisteredSource,
    RegistrationResult,
    RegistryStats,
    SourceLifecycleState,
    utc_now_iso,
)
from .errors import (
    InvalidLifecycleTransitionError,
    SourceNotAdmittedError,
    SourceRegistryConflictError,
)
from .repository import SQLiteSourceRegistryRepository


_ALLOWED_TRANSITIONS = {
    SourceLifecycleState.ADMITTED: {
        SourceLifecycleState.ACTIVE,
        SourceLifecycleState.RETIRED,
    },
    SourceLifecycleState.ACTIVE: {
        SourceLifecycleState.PAUSED,
        SourceLifecycleState.RETIRED,
    },
    SourceLifecycleState.PAUSED: {
        SourceLifecycleState.ACTIVE,
        SourceLifecycleState.RETIRED,
    },
    SourceLifecycleState.RETIRED: set(),
}


class SourceRegistryService:
    def __init__(self, db_path: str | Path) -> None:
        self._repository = SQLiteSourceRegistryRepository(db_path)
        self._repository.initialize()

    @property
    def repository(self) -> SQLiteSourceRegistryRepository:
        return self._repository

    def register_admission(
        self,
        decision: AdmissionDecision,
    ) -> RegistrationResult:
        if decision.status is not AdmissionStatus.ACCEPTED:
            raise SourceNotAdmittedError(
                "Only accepted admission decisions may be registered"
            )
        if decision.source is None:
            raise SourceNotAdmittedError(
                "Accepted admission decision contains no normalized source"
            )
        return self.register_source(decision.source)

    def register_source(
        self,
        source: NormalizedSource,
    ) -> RegistrationResult:
        existing_by_fingerprint = self._repository.get_by_fingerprint(
            source.fingerprint
        )
        if existing_by_fingerprint is not None:
            return RegistrationResult(
                source=existing_by_fingerprint,
                created=False,
            )

        existing_by_source_id = self._repository.get_by_source_id(
            source.source_id
        )
        if existing_by_source_id is not None:
            raise SourceRegistryConflictError(
                "source_id already exists with a different fingerprint"
            )

        timestamp = utc_now_iso()

        try:
            registered = self._repository.insert(
                source_id=source.source_id,
                display_name=source.display_name,
                canonical_location=source.canonical_location,
                kind=source.kind.value,
                trust_tier=source.trust_tier.value,
                fingerprint=source.fingerprint,
                host=source.host,
                lifecycle_state=SourceLifecycleState.ADMITTED,
                admitted_at=timestamp,
                updated_at=timestamp,
                metadata=dict(source.metadata),
            )
        except sqlite3.IntegrityError as exc:
            raise SourceRegistryConflictError(
                f"Unable to register source: {exc}"
            ) from exc

        return RegistrationResult(
            source=registered,
            created=True,
        )

    def get(self, registry_id: int) -> RegisteredSource:
        return self._repository.get_by_id(registry_id)

    def get_by_source_id(
        self,
        source_id: str,
    ) -> RegisteredSource | None:
        return self._repository.get_by_source_id(source_id)

    def list_sources(self) -> list[RegisteredSource]:
        return self._repository.list_all()

    def transition(
        self,
        registry_id: int,
        target: SourceLifecycleState,
    ) -> RegisteredSource:
        current = self._repository.get_by_id(registry_id)

        if target is current.lifecycle_state:
            return current

        allowed = _ALLOWED_TRANSITIONS[current.lifecycle_state]
        if target not in allowed:
            raise InvalidLifecycleTransitionError(
                f"Invalid source lifecycle transition: "
                f"{current.lifecycle_state.value} -> {target.value}"
            )

        return self._repository.update_state(
            registry_id,
            target,
            utc_now_iso(),
        )

    def stats(self) -> RegistryStats:
        return self._repository.stats()
