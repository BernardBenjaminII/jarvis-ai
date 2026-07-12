"""
Canonical lifecycle and queue-state transitions for JARVIS assimilation.

This service owns coordinated changes to:

- knowledge_registry.lifecycle_state
- knowledge_registry.assimilation_state
- knowledge_assimilation_queue.queue_state
- queue retry and diagnostic fields

It does not select work, extract content, write chunks, manage attempts, or
commit transactions. The caller owns transaction boundaries.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class StateTransitionResult:
    """Result of a coordinated registry and queue transition."""

    registry_rows: int
    queue_rows: int

    @property
    def applied(self) -> bool:
        """Return whether exactly one registry and one queue row changed."""

        return self.registry_rows == 1 and self.queue_rows == 1


class AssimilationStateService:
    """Apply canonical assimilation state transitions."""

    def claim_document(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
        attempt_number: int,
        max_attempts: int,
    ) -> StateTransitionResult:
        """
        Move one validated and queued document into processing.

        The caller should hold a BEGIN IMMEDIATE transaction.
        """

        registry_update = conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='extracting',
                assimilation_state='processing',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND object_type='single_document'
              AND lifecycle_state='validated'
              AND assimilation_state='queued'
            """,
            (object_uuid,),
        )

        queue_update = conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='processing',
                attempt_count=?,
                max_attempts=?,
                last_attempt_at=CURRENT_TIMESTAMP,
                last_error=NULL,
                completed_at=NULL,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND queue_state='queued'
            """,
            (
                attempt_number,
                max_attempts,
                object_uuid,
            ),
        )

        return StateTransitionResult(
            registry_rows=registry_update.rowcount,
            queue_rows=queue_update.rowcount,
        )

    def mark_document_ready_for_embedding(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
    ) -> StateTransitionResult:
        """Complete document chunking and mark it ready for embedding."""

        registry_update = conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='chunked',
                assimilation_state='ready_for_embedding',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND object_type='single_document'
              AND assimilation_state='processing'
            """,
            (object_uuid,),
        )

        queue_update = conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='completed',
                last_error=NULL,
                completed_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND queue_state='processing'
            """,
            (object_uuid,),
        )

        return StateTransitionResult(
            registry_rows=registry_update.rowcount,
            queue_rows=queue_update.rowcount,
        )

    def mark_document_failure(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
        error_text: str,
        retry_exhausted: bool,
    ) -> StateTransitionResult:
        """
        Record a failed document attempt.

        Recoverable failures return to validated/queued. Exhausted documents
        enter terminal failure states.
        """

        if retry_exhausted:
            lifecycle_state = "assimilation_failed"
            assimilation_state = "failed"
            queue_state = "failed"
        else:
            lifecycle_state = "validated"
            assimilation_state = "queued"
            queue_state = "queued"

        registry_update = conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state=?,
                assimilation_state=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND object_type='single_document'
            """,
            (
                lifecycle_state,
                assimilation_state,
                object_uuid,
            ),
        )

        queue_update = conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state=?,
                last_error=?,
                completed_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (
                queue_state,
                error_text,
                object_uuid,
            ),
        )

        return StateTransitionResult(
            registry_rows=registry_update.rowcount,
            queue_rows=queue_update.rowcount,
        )

    def recover_stale_document(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
    ) -> StateTransitionResult:
        """Return a stale processing claim to validated/queued."""

        registry_update = conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='validated',
                assimilation_state='queued',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND object_type='single_document'
            """,
            (object_uuid,),
        )

        queue_update = conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='queued',
                last_error='Recovered stale processing claim',
                completed_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        return StateTransitionResult(
            registry_rows=registry_update.rowcount,
            queue_rows=queue_update.rowcount,
        )

    def fail_stale_exhausted_document(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
    ) -> StateTransitionResult:
        """Place an exhausted stale claim in terminal failure state."""

        registry_update = conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='assimilation_failed',
                assimilation_state='failed',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND object_type='single_document'
            """,
            (object_uuid,),
        )

        queue_update = conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='failed',
                last_error='Stale processing claim exhausted retry limit',
                completed_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        return StateTransitionResult(
            registry_rows=registry_update.rowcount,
            queue_rows=queue_update.rowcount,
        )

    def requeue_failed_document(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
        reset_attempts: bool,
    ) -> StateTransitionResult:
        """Explicitly return a failed document to validated/queued."""

        registry_update = conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='validated',
                assimilation_state='queued',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
              AND object_type='single_document'
              AND assimilation_state='failed'
            """,
            (object_uuid,),
        )

        if reset_attempts:
            queue_update = conn.execute(
                """
                UPDATE knowledge_assimilation_queue
                SET queue_state='queued',
                    attempt_count=0,
                    last_error=NULL,
                    last_attempt_at=NULL,
                    completed_at=NULL,
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
            )
        else:
            queue_update = conn.execute(
                """
                UPDATE knowledge_assimilation_queue
                SET queue_state='queued',
                    completed_at=NULL,
                    updated_at=CURRENT_TIMESTAMP
                WHERE object_uuid=?
                """,
                (object_uuid,),
            )

        return StateTransitionResult(
            registry_rows=registry_update.rowcount,
            queue_rows=queue_update.rowcount,
        )
