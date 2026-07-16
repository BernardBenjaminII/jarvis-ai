"""
Bounded canonical acquisition-to-assimilation dispatch.

The dispatcher:

1. atomically claims queued acquisition handoffs
2. resolves the canonical Knowledge Registry object UUID
3. invokes Phase VI through its public execution port
4. records successful or failed dispatch outcomes

The dispatcher contains no Phase VI SQL and no extraction logic.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from knowledge_engine.acquisition.dispatch.models import (
    AssimilationDispatchResult,
)
from knowledge_engine.acquisition.dispatch.ports import (
    AcquisitionRegistrationPort,
    PhaseVIExecutionPort,
)
from knowledge_engine.acquisition.dispatch.repository import (
    AssimilationDispatchRepository,
)
from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffRecord,
)


class CanonicalAssimilationDispatcher:
    """Dispatch a bounded batch of queued acquisition handoffs."""

    def __init__(
        self,
        *,
        registration_port: AcquisitionRegistrationPort,
        execution_port: PhaseVIExecutionPort,
        repository: AssimilationDispatchRepository | None = None,
    ) -> None:
        self.registration_port = registration_port
        self.execution_port = execution_port
        self.repository = (
            repository
            if repository is not None
            else AssimilationDispatchRepository()
        )

    def dispatch(
        self,
        *,
        conn: sqlite3.Connection,
        limit: int = 25,
        stop_on_error: bool = False,
        timestamp: str | None = None,
    ) -> AssimilationDispatchResult:
        """
        Dispatch up to limit queued handoffs.

        Registration and Phase VI execution occur outside the repository's
        short claim transaction. Each resulting state transition is then
        persisted independently.
        """

        if not isinstance(conn, sqlite3.Connection):
            raise TypeError(
                "conn must be a sqlite3.Connection"
            )

        if limit < 1:
            raise ValueError(
                "limit must be at least 1"
            )

        resolved_timestamp = (
            timestamp.strip()
            if timestamp is not None
            else datetime.now(
                timezone.utc
            ).isoformat()
        )

        if not resolved_timestamp:
            raise ValueError(
                "timestamp must not be empty"
            )

        claimed = self.repository.claim_queued(
            conn=conn,
            limit=limit,
            claimed_at=resolved_timestamp,
        )

        completed: list[
            AssimilationHandoffRecord
        ] = []

        dispatched_count = 0
        failed_count = 0
        skipped_count = 0

        for index, handoff in enumerate(claimed):
            try:
                object_uuid = (
                    self.registration_port
                    .ensure_registered(
                        handoff=handoff,
                    )
                )

                if not isinstance(
                    object_uuid,
                    str,
                ):
                    raise TypeError(
                        "Registration port returned a "
                        "non-string object UUID"
                    )

                normalized_object_uuid = (
                    object_uuid.strip()
                )

                if not normalized_object_uuid:
                    raise RuntimeError(
                        "Registration port returned an "
                        "empty object UUID"
                    )

                execution_result = (
                    self.execution_port
                    .execute_registered_object(
                        object_uuid=(
                            normalized_object_uuid
                        ),
                    )
                )

                if not isinstance(
                    execution_result,
                    dict,
                ):
                    raise TypeError(
                        "Execution port returned a "
                        "non-dictionary result"
                    )

                processed = int(
                    execution_result.get(
                        "processed",
                        0,
                    )
                )

                failed = int(
                    execution_result.get(
                        "failed",
                        0,
                    )
                )

                returned_uuid = (
                    execution_result.get(
                        "object_uuid"
                    )
                )

                if processed == 1:
                    if returned_uuid != (
                        normalized_object_uuid
                    ):
                        raise RuntimeError(
                            "Phase VI returned a different "
                            "object UUID than the registered "
                            "handoff object"
                        )

                    updated = (
                        self.repository
                        .mark_dispatched(
                            conn=conn,
                            handoff_id=(
                                handoff.handoff_id
                            ),
                            object_uuid=(
                                normalized_object_uuid
                            ),
                            updated_at=(
                                resolved_timestamp
                            ),
                        )
                    )

                    dispatched_count += 1
                    completed.append(updated)

                    continue

                if failed == 1:
                    error_message = str(
                        execution_result.get(
                            "error"
                        )
                        or execution_result.get(
                            "message"
                        )
                        or (
                            "Phase VI reported an "
                            "assimilation failure"
                        )
                    )

                else:
                    error_message = str(
                        execution_result.get(
                            "message"
                        )
                        or (
                            "Phase VI did not process the "
                            "registered object"
                        )
                    )

                updated = (
                    self.repository.mark_failed(
                        conn=conn,
                        handoff_id=(
                            handoff.handoff_id
                        ),
                        error=error_message,
                        updated_at=(
                            resolved_timestamp
                        ),
                    )
                )

                failed_count += 1
                completed.append(updated)

            except Exception as exc:
                updated = (
                    self.repository.mark_failed(
                        conn=conn,
                        handoff_id=(
                            handoff.handoff_id
                        ),
                        error=(
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                        updated_at=(
                            resolved_timestamp
                        ),
                    )
                )

                failed_count += 1
                completed.append(updated)

            if (
                stop_on_error
                and completed[-1].handoff_state.value
                == "failed"
            ):
                remaining = claimed[
                    index + 1:
                ]

                released = (
                    self.repository.release_claims(
                        conn=conn,
                        handoff_ids=(
                            item.handoff_id
                            for item in remaining
                        ),
                        updated_at=(
                            resolved_timestamp
                        ),
                        reason=(
                            "Dispatch batch stopped after "
                            "an earlier failure"
                        ),
                    )
                )

                skipped_count += len(released)
                completed.extend(released)

                break

        return AssimilationDispatchResult(
            claimed=len(claimed),
            dispatched=dispatched_count,
            failed=failed_count,
            skipped=skipped_count,
            handoffs=tuple(completed),
        )

    def requeue_failed(
        self,
        *,
        conn: sqlite3.Connection,
        limit: int = 25,
        max_attempts: int = 3,
        timestamp: str | None = None,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        """Requeue retryable failed handoffs."""

        resolved_timestamp = (
            timestamp.strip()
            if timestamp is not None
            else datetime.now(
                timezone.utc
            ).isoformat()
        )

        if not resolved_timestamp:
            raise ValueError(
                "timestamp must not be empty"
            )

        return self.repository.requeue_failed(
            conn=conn,
            limit=limit,
            max_attempts=max_attempts,
            updated_at=resolved_timestamp,
        )

    def recover_stale_claims(
        self,
        *,
        conn: sqlite3.Connection,
        stale_after_minutes: int = 30,
        now: datetime | None = None,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        """Recover interrupted dispatching rows."""

        return (
            self.repository
            .recover_stale_dispatching(
                conn=conn,
                stale_after_minutes=(
                    stale_after_minutes
                ),
                now=now,
            )
        )


__all__ = [
    "CanonicalAssimilationDispatcher",
]
