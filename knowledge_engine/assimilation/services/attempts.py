"""
Canonical attempt-journal operations for JARVIS assimilation.

This service owns writes to:

- knowledge_assimilation_attempts

It does not:

- open database connections
- begin transactions
- commit or roll back transactions
- select queue work
- modify registry or queue state
- persist extracted document content

The caller owns transaction boundaries.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class AttemptStartResult:
    """Result returned when an assimilation attempt is created."""

    attempt_id: int
    object_uuid: str
    attempt_number: int
    attempt_state: str = "processing"


@dataclass(frozen=True)
class AttemptUpdateResult:
    """Result returned when attempt rows are updated."""

    rows_updated: int
    attempt_state: str

    @property
    def applied(self) -> bool:
        return self.rows_updated > 0


class AttemptJournalService:
    """Create and update durable assimilation-attempt records."""

    def start_attempt(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
        object_path: str,
        object_type: str,
        handler_name: str,
        attempt_number: int,
    ) -> AttemptStartResult:
        """Create one processing attempt and return its durable ID."""

        if not object_uuid.strip():
            raise ValueError("object_uuid must not be empty")

        if not object_path.strip():
            raise ValueError("object_path must not be empty")

        if not object_type.strip():
            raise ValueError("object_type must not be empty")

        if not handler_name.strip():
            raise ValueError("handler_name must not be empty")

        if attempt_number < 1:
            raise ValueError("attempt_number must be at least 1")

        cursor = conn.execute(
            """
            INSERT INTO knowledge_assimilation_attempts (
                object_uuid,
                object_path,
                object_type,
                handler_name,
                attempt_number,
                attempt_state
            )
            VALUES (?, ?, ?, ?, ?, 'processing')
            """,
            (
                object_uuid,
                object_path,
                object_type,
                handler_name,
                attempt_number,
            ),
        )

        attempt_id = int(cursor.lastrowid)

        return AttemptStartResult(
            attempt_id=attempt_id,
            object_uuid=object_uuid,
            attempt_number=attempt_number,
        )

    def complete_attempt(
        self,
        *,
        conn: sqlite3.Connection,
        attempt_id: int,
        text_chars: int,
        chunk_count: int,
        checksum: str,
    ) -> AttemptUpdateResult:
        """Mark one attempt completed and store output statistics."""

        if attempt_id < 1:
            raise ValueError("attempt_id must be at least 1")

        if text_chars < 1:
            raise ValueError("text_chars must be at least 1")

        if chunk_count < 1:
            raise ValueError("chunk_count must be at least 1")

        if not checksum.strip():
            raise ValueError("checksum must not be empty")

        cursor = conn.execute(
            """
            UPDATE knowledge_assimilation_attempts
            SET attempt_state='completed',
                completed_at=CURRENT_TIMESTAMP,
                text_chars=?,
                chunk_count=?,
                checksum=?,
                error_type=NULL,
                error_message=NULL
            WHERE attempt_id=?
              AND attempt_state='processing'
            """,
            (
                text_chars,
                chunk_count,
                checksum,
                attempt_id,
            ),
        )

        return AttemptUpdateResult(
            rows_updated=cursor.rowcount,
            attempt_state="completed",
        )

    def fail_attempt(
        self,
        *,
        conn: sqlite3.Connection,
        attempt_id: int,
        error_type: str,
        error_message: str,
    ) -> AttemptUpdateResult:
        """Mark one active attempt failed with structured diagnostics."""

        if attempt_id < 1:
            raise ValueError("attempt_id must be at least 1")

        if not error_type.strip():
            raise ValueError("error_type must not be empty")

        if not error_message.strip():
            raise ValueError("error_message must not be empty")

        cursor = conn.execute(
            """
            UPDATE knowledge_assimilation_attempts
            SET attempt_state='failed',
                completed_at=CURRENT_TIMESTAMP,
                error_type=?,
                error_message=?
            WHERE attempt_id=?
              AND attempt_state='processing'
            """,
            (
                error_type,
                error_message,
                attempt_id,
            ),
        )

        return AttemptUpdateResult(
            rows_updated=cursor.rowcount,
            attempt_state="failed",
        )

    def abandon_processing_attempts(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
        reason: str = "Recovered stale processing claim",
    ) -> AttemptUpdateResult:
        """Mark all active attempts for one object as abandoned."""

        if not object_uuid.strip():
            raise ValueError("object_uuid must not be empty")

        cursor = conn.execute(
            """
            UPDATE knowledge_assimilation_attempts
            SET attempt_state='abandoned',
                completed_at=CURRENT_TIMESTAMP,
                error_type='StaleProcessingRecovery',
                error_message=?
            WHERE object_uuid=?
              AND attempt_state='processing'
            """,
            (
                reason,
                object_uuid,
            ),
        )

        return AttemptUpdateResult(
            rows_updated=cursor.rowcount,
            attempt_state="abandoned",
        )

    def fail_stale_exhausted_attempts(
        self,
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
        reason: str = "Stale processing claim exhausted retry limit",
    ) -> AttemptUpdateResult:
        """Fail all active attempts for a retry-exhausted stale object."""

        if not object_uuid.strip():
            raise ValueError("object_uuid must not be empty")

        cursor = conn.execute(
            """
            UPDATE knowledge_assimilation_attempts
            SET attempt_state='failed',
                completed_at=CURRENT_TIMESTAMP,
                error_type='StaleProcessingRetryExhausted',
                error_message=?
            WHERE object_uuid=?
              AND attempt_state='processing'
            """,
            (
                reason,
                object_uuid,
            ),
        )

        return AttemptUpdateResult(
            rows_updated=cursor.rowcount,
            attempt_state="failed",
        )
