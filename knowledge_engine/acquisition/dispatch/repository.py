"""
Persistence and lifecycle transitions for assimilation dispatch.

This repository owns only the acquisition handoff table:

    acquisition_assimilation_handoffs

It does not:

- register Knowledge Registry objects
- access Phase VI assimilation tables
- perform extraction
- invoke handlers
- create database connections
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone

from knowledge_engine.acquisition.handoff.models import (
    AssimilationHandoffRecord,
    AssimilationHandoffState,
)
from knowledge_engine.acquisition.handoff.repository import (
    AssimilationHandoffRepository,
)
from knowledge_engine.acquisition.handoff.schema import (
    ensure_assimilation_handoff_schema,
)


class AssimilationDispatchRepository:
    """
    Claim and transition acquisition-to-assimilation handoffs.

    Public operations use short transactions because registration and Phase VI
    execution occur outside this repository.
    """

    def __init__(
        self,
        handoff_repository: AssimilationHandoffRepository | None = None,
    ) -> None:
        self.handoff_repository = (
            handoff_repository
            if handoff_repository is not None
            else AssimilationHandoffRepository()
        )

    def claim_queued(
        self,
        *,
        conn: sqlite3.Connection,
        limit: int,
        claimed_at: str,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        """
        Atomically claim a bounded group of queued handoffs.

        Claimed rows transition:

            queued -> dispatching

        The dispatch attempt count increases exactly once per successful claim.
        """

        if limit < 1:
            raise ValueError(
                "limit must be at least 1"
            )

        normalized_timestamp = claimed_at.strip()

        if not normalized_timestamp:
            raise ValueError(
                "claimed_at must not be empty"
            )

        ensure_assimilation_handoff_schema(conn)

        conn.execute("BEGIN IMMEDIATE")

        try:
            rows = conn.execute(
                """
                SELECT handoff_id
                FROM acquisition_assimilation_handoffs
                WHERE handoff_state='queued'
                ORDER BY
                    created_at ASC,
                    handoff_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

            handoff_ids = tuple(
                str(row[0])
                for row in rows
            )

            for handoff_id in handoff_ids:
                cursor = conn.execute(
                    """
                    UPDATE acquisition_assimilation_handoffs
                    SET
                        handoff_state='dispatching',
                        updated_at=?,
                        dispatch_attempt_count=(
                            dispatch_attempt_count + 1
                        ),
                        last_error=NULL
                    WHERE handoff_id=?
                      AND handoff_state='queued'
                    """,
                    (
                        normalized_timestamp,
                        handoff_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Failed to atomically claim handoff "
                        f"{handoff_id}"
                    )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        return tuple(
            self.handoff_repository.get_handoff(
                conn=conn,
                handoff_id=handoff_id,
            )
            for handoff_id in handoff_ids
        )

    def mark_dispatched(
        self,
        *,
        conn: sqlite3.Connection,
        handoff_id: str,
        object_uuid: str,
        updated_at: str,
    ) -> AssimilationHandoffRecord:
        """
        Mark one claimed handoff as successfully dispatched.

        Transition:

            dispatching -> dispatched
        """

        normalized_handoff_id = handoff_id.strip()
        normalized_object_uuid = object_uuid.strip()
        normalized_timestamp = updated_at.strip()

        if not normalized_handoff_id:
            raise ValueError(
                "handoff_id must not be empty"
            )

        if not normalized_object_uuid:
            raise ValueError(
                "object_uuid must not be empty"
            )

        if not normalized_timestamp:
            raise ValueError(
                "updated_at must not be empty"
            )

        conn.execute("BEGIN IMMEDIATE")

        try:
            cursor = conn.execute(
                """
                UPDATE acquisition_assimilation_handoffs
                SET
                    handoff_state='dispatched',
                    updated_at=?,
                    assimilation_reference=?,
                    last_error=NULL
                WHERE handoff_id=?
                  AND handoff_state='dispatching'
                """,
                (
                    normalized_timestamp,
                    normalized_object_uuid,
                    normalized_handoff_id,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Handoff is not eligible for successful dispatch: "
                    f"{normalized_handoff_id}"
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        return self.handoff_repository.get_handoff(
            conn=conn,
            handoff_id=normalized_handoff_id,
        )

    def mark_failed(
        self,
        *,
        conn: sqlite3.Connection,
        handoff_id: str,
        error: str,
        updated_at: str,
    ) -> AssimilationHandoffRecord:
        """
        Record a dispatch failure.

        Transition:

            dispatching -> failed
        """

        normalized_handoff_id = handoff_id.strip()
        normalized_timestamp = updated_at.strip()
        normalized_error = error.strip()

        if not normalized_handoff_id:
            raise ValueError(
                "handoff_id must not be empty"
            )

        if not normalized_timestamp:
            raise ValueError(
                "updated_at must not be empty"
            )

        if not normalized_error:
            normalized_error = (
                "Unknown assimilation dispatch failure"
            )

        conn.execute("BEGIN IMMEDIATE")

        try:
            cursor = conn.execute(
                """
                UPDATE acquisition_assimilation_handoffs
                SET
                    handoff_state='failed',
                    updated_at=?,
                    last_error=?
                WHERE handoff_id=?
                  AND handoff_state='dispatching'
                """,
                (
                    normalized_timestamp,
                    normalized_error,
                    normalized_handoff_id,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Handoff is not eligible for failure recording: "
                    f"{normalized_handoff_id}"
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        return self.handoff_repository.get_handoff(
            conn=conn,
            handoff_id=normalized_handoff_id,
        )

    def release_claims(
        self,
        *,
        conn: sqlite3.Connection,
        handoff_ids: Iterable[str],
        updated_at: str,
        reason: str = "Dispatch batch stopped before execution",
    ) -> tuple[AssimilationHandoffRecord, ...]:
        """
        Return unprocessed claims to queued.

        This is used when stop_on_error halts a bounded batch after one item
        fails. Attempt counts remain incremented because the rows were claimed,
        but they remain eligible for a later dispatcher run.

        Transition:

            dispatching -> queued
        """

        normalized_ids = tuple(
            handoff_id.strip()
            for handoff_id in handoff_ids
            if handoff_id.strip()
        )

        if len(normalized_ids) != len(
            set(normalized_ids)
        ):
            raise ValueError(
                "handoff_ids must be unique"
            )

        normalized_timestamp = updated_at.strip()
        normalized_reason = reason.strip()

        if not normalized_timestamp:
            raise ValueError(
                "updated_at must not be empty"
            )

        if not normalized_reason:
            raise ValueError(
                "reason must not be empty"
            )

        if not normalized_ids:
            return ()

        conn.execute("BEGIN IMMEDIATE")

        try:
            for handoff_id in normalized_ids:
                cursor = conn.execute(
                    """
                    UPDATE acquisition_assimilation_handoffs
                    SET
                        handoff_state='queued',
                        updated_at=?,
                        last_error=?
                    WHERE handoff_id=?
                      AND handoff_state='dispatching'
                    """,
                    (
                        normalized_timestamp,
                        normalized_reason,
                        handoff_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Handoff claim could not be released: "
                        f"{handoff_id}"
                    )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        return tuple(
            self.handoff_repository.get_handoff(
                conn=conn,
                handoff_id=handoff_id,
            )
            for handoff_id in normalized_ids
        )

    def requeue_failed(
        self,
        *,
        conn: sqlite3.Connection,
        limit: int,
        max_attempts: int,
        updated_at: str,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        """
        Requeue failed handoffs below the configured attempt limit.

        Transition:

            failed -> queued
        """

        if limit < 1:
            raise ValueError(
                "limit must be at least 1"
            )

        if max_attempts < 1:
            raise ValueError(
                "max_attempts must be at least 1"
            )

        normalized_timestamp = updated_at.strip()

        if not normalized_timestamp:
            raise ValueError(
                "updated_at must not be empty"
            )

        conn.execute("BEGIN IMMEDIATE")

        try:
            rows = conn.execute(
                """
                SELECT handoff_id
                FROM acquisition_assimilation_handoffs
                WHERE handoff_state='failed'
                  AND dispatch_attempt_count < ?
                ORDER BY
                    updated_at ASC,
                    handoff_id ASC
                LIMIT ?
                """,
                (
                    max_attempts,
                    limit,
                ),
            ).fetchall()

            handoff_ids = tuple(
                str(row[0])
                for row in rows
            )

            for handoff_id in handoff_ids:
                cursor = conn.execute(
                    """
                    UPDATE acquisition_assimilation_handoffs
                    SET
                        handoff_state='queued',
                        updated_at=?,
                        last_error=NULL
                    WHERE handoff_id=?
                      AND handoff_state='failed'
                      AND dispatch_attempt_count < ?
                    """,
                    (
                        normalized_timestamp,
                        handoff_id,
                        max_attempts,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Failed handoff could not be requeued: "
                        f"{handoff_id}"
                    )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        return tuple(
            self.handoff_repository.get_handoff(
                conn=conn,
                handoff_id=handoff_id,
            )
            for handoff_id in handoff_ids
        )

    def recover_stale_dispatching(
        self,
        *,
        conn: sqlite3.Connection,
        stale_after_minutes: int,
        now: datetime | None = None,
    ) -> tuple[AssimilationHandoffRecord, ...]:
        """
        Recover interrupted dispatch claims.

        Transition:

            dispatching -> queued
        """

        if stale_after_minutes < 1:
            raise ValueError(
                "stale_after_minutes must be at least 1"
            )

        resolved_now = (
            now
            if now is not None
            else datetime.now(timezone.utc)
        )

        if resolved_now.tzinfo is None:
            raise ValueError(
                "now must be timezone-aware"
            )

        cutoff = (
            resolved_now
            - timedelta(
                minutes=stale_after_minutes
            )
        ).isoformat()

        updated_at = resolved_now.isoformat()

        conn.execute("BEGIN IMMEDIATE")

        try:
            rows = conn.execute(
                """
                SELECT handoff_id
                FROM acquisition_assimilation_handoffs
                WHERE handoff_state='dispatching'
                  AND updated_at < ?
                ORDER BY
                    updated_at ASC,
                    handoff_id ASC
                """,
                (cutoff,),
            ).fetchall()

            handoff_ids = tuple(
                str(row[0])
                for row in rows
            )

            for handoff_id in handoff_ids:
                cursor = conn.execute(
                    """
                    UPDATE acquisition_assimilation_handoffs
                    SET
                        handoff_state='queued',
                        updated_at=?,
                        last_error=(
                            'Recovered interrupted dispatch claim'
                        )
                    WHERE handoff_id=?
                      AND handoff_state='dispatching'
                    """,
                    (
                        updated_at,
                        handoff_id,
                    ),
                )

                if cursor.rowcount != 1:
                    raise RuntimeError(
                        "Stale handoff claim could not be recovered: "
                        f"{handoff_id}"
                    )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        return tuple(
            self.handoff_repository.get_handoff(
                conn=conn,
                handoff_id=handoff_id,
            )
            for handoff_id in handoff_ids
        )

    def count_by_state(
        self,
        *,
        conn: sqlite3.Connection,
        state: AssimilationHandoffState,
    ) -> int:
        """Return the number of handoffs in one lifecycle state."""

        if not isinstance(
            state,
            AssimilationHandoffState,
        ):
            raise TypeError(
                "state must be an AssimilationHandoffState"
            )

        ensure_assimilation_handoff_schema(conn)

        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM acquisition_assimilation_handoffs
            WHERE handoff_state=?
            """,
            (state.value,),
        ).fetchone()

        return int(row[0])

    def inventory(
        self,
        *,
        conn: sqlite3.Connection,
    ) -> dict[str, int]:
        """Return deterministic handoff counts by lifecycle state."""

        return {
            state.value: self.count_by_state(
                conn=conn,
                state=state,
            )
            for state in AssimilationHandoffState
        }


__all__ = [
    "AssimilationDispatchRepository",
]
