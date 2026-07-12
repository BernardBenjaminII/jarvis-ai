"""
Failure-safe execution engine for JARVIS document assimilation.

The runner currently coordinates:

1. Work selection and atomic claim transactions
2. Text extraction and chunking
3. Document and chunk persistence
4. Attempt-journal bookkeeping
5. Stale-work and retry recovery

Lifecycle and queue transitions are delegated to AssimilationStateService.
Later VI-E milestones will extract the remaining responsibilities.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from knowledge_engine.assimilation.schema import (
    ensure_assimilation_runtime_schema,
)
from knowledge_engine.assimilation.services.state import (
    AssimilationStateService,
)
from knowledge_engine.assimilation.single_document import (
    checksum,
    chunk_text,
    read_text,
)


@dataclass(frozen=True)
class ClaimedDocument:
    """A single registry object atomically claimed for assimilation."""

    object_uuid: str
    object_path: str
    object_type: str
    attempt_number: int
    max_attempts: int
    attempt_id: int


class AssimilationRunner:
    """Execute failure-safe single-document assimilation work."""

    HANDLER_NAME = "document_assimilation"

    def __init__(
        self,
        db: Any,
        *,
        default_max_attempts: int = 3,
        state_service: AssimilationStateService | None = None,
    ):
        if default_max_attempts < 1:
            raise ValueError("default_max_attempts must be at least 1")

        self.db = db
        self.default_max_attempts = default_max_attempts
        self.state_service = state_service or AssimilationStateService()

    def run_one_single_document(
        self,
        *,
        expected_object_uuid: str | None = None,
    ) -> dict[str, Any]:
        """Claim and process one validated and queued document."""

        claim = self._claim_single_document(
            expected_object_uuid=expected_object_uuid,
        )

        if claim is None:
            return {
                "processed": 0,
                "message": (
                    "no eligible validated and queued single_document "
                    "object found"
                ),
            }

        path = Path(claim.object_path).expanduser()

        try:
            self._validate_source_path(path)

            text = read_text(path)
            normalized_text = text.strip()

            if not normalized_text:
                raise RuntimeError(
                    f"Document extraction produced no usable text: {path}"
                )

            text_checksum = checksum(normalized_text)
            chunks = chunk_text(normalized_text)

            if not chunks:
                raise RuntimeError(
                    f"Document chunking produced no usable chunks: {path}"
                )

            self._complete_success(
                claim=claim,
                text=normalized_text,
                text_checksum=text_checksum,
                chunks=chunks,
            )

        except Exception as exc:
            failure_result = self._complete_failure(
                claim=claim,
                error=exc,
            )

            return {
                "processed": 0,
                "failed": 1,
                "object_uuid": claim.object_uuid,
                "document_path": claim.object_path,
                "attempt_number": claim.attempt_number,
                "max_attempts": claim.max_attempts,
                **failure_result,
            }

        return {
            "processed": 1,
            "failed": 0,
            "object_uuid": claim.object_uuid,
            "document_path": claim.object_path,
            "attempt_number": claim.attempt_number,
            "max_attempts": claim.max_attempts,
            "text_chars": len(normalized_text),
            "chunks": len(chunks),
            "checksum": text_checksum,
        }

    def recover_stale_processing(
        self,
        *,
        stale_after_minutes: int = 30,
    ) -> dict[str, Any]:
        """Recover document records left in stale processing states."""

        if stale_after_minutes < 1:
            raise ValueError("stale_after_minutes must be at least 1")

        cutoff = (
            datetime.now(timezone.utc)
            - timedelta(minutes=stale_after_minutes)
        ).strftime("%Y-%m-%d %H:%M:%S")

        recovered = 0
        exhausted = 0
        recovered_uuids: list[str] = []
        exhausted_uuids: list[str] = []

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            rows = conn.execute(
                """
                SELECT
                    r.object_uuid,
                    COALESCE(q.attempt_count, 0) AS attempt_count,
                    COALESCE(q.max_attempts, ?) AS max_attempts
                FROM knowledge_registry AS r
                JOIN knowledge_assimilation_queue AS q
                  ON q.object_uuid = r.object_uuid
                WHERE r.object_type='single_document'
                  AND (
                        r.assimilation_state='processing'
                        OR q.queue_state='processing'
                  )
                  AND COALESCE(q.updated_at, r.updated_at) < ?
                ORDER BY
                    COALESCE(q.updated_at, r.updated_at) ASC,
                    r.object_uuid ASC
                """,
                (
                    self.default_max_attempts,
                    cutoff,
                ),
            ).fetchall()

            for row in rows:
                object_uuid = str(row["object_uuid"])
                attempt_count = int(row["attempt_count"])
                max_attempts = int(row["max_attempts"])

                if attempt_count >= max_attempts:
                    transition = (
                        self.state_service.fail_stale_exhausted_document(
                            conn=conn,
                            object_uuid=object_uuid,
                        )
                    )

                    if not transition.applied:
                        raise RuntimeError(
                            "Failed exhausted stale transition for "
                            f"{object_uuid}"
                        )

                    self._fail_processing_attempts_as_stale_exhausted(
                        conn=conn,
                        object_uuid=object_uuid,
                    )

                    exhausted += 1
                    exhausted_uuids.append(object_uuid)

                else:
                    transition = self.state_service.recover_stale_document(
                        conn=conn,
                        object_uuid=object_uuid,
                    )

                    if not transition.applied:
                        raise RuntimeError(
                            "Failed stale recovery transition for "
                            f"{object_uuid}"
                        )

                    self._abandon_processing_attempts(
                        conn=conn,
                        object_uuid=object_uuid,
                    )

                    recovered += 1
                    recovered_uuids.append(object_uuid)

            conn.commit()

        return {
            "stale_after_minutes": stale_after_minutes,
            "cutoff": cutoff,
            "recovered": recovered,
            "exhausted": exhausted,
            "recovered_object_uuids": recovered_uuids,
            "exhausted_object_uuids": exhausted_uuids,
        }

    def requeue_failed_documents(
        self,
        *,
        limit: int = 25,
        reset_attempts: bool = False,
    ) -> dict[str, Any]:
        """Requeue failed documents that satisfy the retry policy."""

        if limit < 1:
            raise ValueError("limit must be at least 1")

        requeued: list[str] = []

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            if reset_attempts:
                rows = conn.execute(
                    """
                    SELECT r.object_uuid
                    FROM knowledge_registry AS r
                    JOIN knowledge_assimilation_queue AS q
                      ON q.object_uuid = r.object_uuid
                    WHERE r.object_type='single_document'
                      AND r.assimilation_state='failed'
                    ORDER BY q.updated_at ASC, r.object_uuid ASC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT r.object_uuid
                    FROM knowledge_registry AS r
                    JOIN knowledge_assimilation_queue AS q
                      ON q.object_uuid = r.object_uuid
                    WHERE r.object_type='single_document'
                      AND r.assimilation_state='failed'
                      AND COALESCE(q.attempt_count, 0)
                          < COALESCE(q.max_attempts, ?)
                    ORDER BY q.updated_at ASC, r.object_uuid ASC
                    LIMIT ?
                    """,
                    (
                        self.default_max_attempts,
                        limit,
                    ),
                ).fetchall()

            for row in rows:
                object_uuid = str(row["object_uuid"])

                transition = self.state_service.requeue_failed_document(
                    conn=conn,
                    object_uuid=object_uuid,
                    reset_attempts=reset_attempts,
                )

                if not transition.applied:
                    raise RuntimeError(
                        f"Failed to requeue document {object_uuid}"
                    )

                requeued.append(object_uuid)

            conn.commit()

        return {
            "requeued": len(requeued),
            "reset_attempts": reset_attempts,
            "object_uuids": requeued,
        }

    def _claim_single_document(
        self,
        *,
        expected_object_uuid: str | None,
    ) -> ClaimedDocument | None:
        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            parameters: list[Any] = [
                self.default_max_attempts,
                self.default_max_attempts,
            ]

            query = """
                SELECT
                    r.object_uuid,
                    r.object_path,
                    r.object_type,
                    COALESCE(q.attempt_count, 0) AS attempt_count,
                    COALESCE(q.max_attempts, ?) AS max_attempts
                FROM knowledge_registry AS r
                JOIN knowledge_assimilation_queue AS q
                  ON q.object_uuid = r.object_uuid
                WHERE r.lifecycle_state='validated'
                  AND r.assimilation_state='queued'
                  AND r.object_type='single_document'
                  AND q.queue_state='queued'
                  AND COALESCE(q.attempt_count, 0)
                      < COALESCE(q.max_attempts, ?)
            """

            if expected_object_uuid is not None:
                query += " AND r.object_uuid=?"
                parameters.append(expected_object_uuid)

            query += """
                ORDER BY r.updated_at ASC, r.object_uuid ASC
                LIMIT 1
            """

            row = conn.execute(
                query,
                tuple(parameters),
            ).fetchone()

            if row is None:
                conn.rollback()
                return None

            object_uuid = str(row["object_uuid"])
            object_path = str(row["object_path"])
            object_type = str(row["object_type"])

            previous_attempts = int(row["attempt_count"])
            attempt_number = previous_attempts + 1

            if previous_attempts == 0:
                max_attempts = self.default_max_attempts
            else:
                max_attempts = int(row["max_attempts"])

            transition = self.state_service.claim_document(
                conn=conn,
                object_uuid=object_uuid,
                attempt_number=attempt_number,
                max_attempts=max_attempts,
            )

            if not transition.applied:
                conn.rollback()
                return None

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
                    self.HANDLER_NAME,
                    attempt_number,
                ),
            )

            attempt_id = int(cursor.lastrowid)
            conn.commit()

        return ClaimedDocument(
            object_uuid=object_uuid,
            object_path=object_path,
            object_type=object_type,
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            attempt_id=attempt_id,
        )

    def _complete_success(
        self,
        *,
        claim: ClaimedDocument,
        text: str,
        text_checksum: str,
        chunks: list[str],
    ) -> None:
        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            conn.execute(
                """
                INSERT INTO document_text (
                    document_path,
                    extractor,
                    text,
                    checksum,
                    status,
                    error
                )
                VALUES (?, ?, ?, ?, 'extracted', NULL)
                ON CONFLICT(document_path) DO UPDATE SET
                    extractor=excluded.extractor,
                    text=excluded.text,
                    checksum=excluded.checksum,
                    status=excluded.status,
                    error=NULL,
                    extracted_at=CURRENT_TIMESTAMP
                """,
                (
                    claim.object_path,
                    "single_document_assimilation",
                    text,
                    text_checksum,
                ),
            )

            conn.execute(
                """
                DELETE FROM chunks
                WHERE document_path=?
                """,
                (claim.object_path,),
            )

            for index, chunk in enumerate(chunks):
                conn.execute(
                    """
                    INSERT INTO chunks (
                        document_path,
                        chunk_index,
                        text,
                        source_page,
                        structure_title
                    )
                    VALUES (?, ?, ?, NULL, NULL)
                    """,
                    (
                        claim.object_path,
                        index,
                        chunk,
                    ),
                )

            transition = (
                self.state_service.mark_document_ready_for_embedding(
                    conn=conn,
                    object_uuid=claim.object_uuid,
                )
            )

            if not transition.applied:
                raise RuntimeError(
                    "Success transition rejected for "
                    f"{claim.object_uuid}"
                )

            conn.execute(
                """
                UPDATE knowledge_assimilation_attempts
                SET attempt_state='completed',
                    completed_at=CURRENT_TIMESTAMP,
                    text_chars=?,
                    chunk_count=?,
                    checksum=?
                WHERE attempt_id=?
                """,
                (
                    len(text),
                    len(chunks),
                    text_checksum,
                    claim.attempt_id,
                ),
            )

            conn.commit()

    def _complete_failure(
        self,
        *,
        claim: ClaimedDocument,
        error: Exception,
    ) -> dict[str, Any]:
        error_type = type(error).__name__
        error_message = str(error)
        exhausted = claim.attempt_number >= claim.max_attempts

        with self.db.connect() as conn:
            ensure_assimilation_runtime_schema(conn)
            conn.execute("BEGIN IMMEDIATE")

            transition = self.state_service.mark_document_failure(
                conn=conn,
                object_uuid=claim.object_uuid,
                error_text=f"{error_type}: {error_message}",
                retry_exhausted=exhausted,
            )

            if not transition.applied:
                raise RuntimeError(
                    "Failure transition rejected for "
                    f"{claim.object_uuid}"
                )

            conn.execute(
                """
                UPDATE knowledge_assimilation_attempts
                SET attempt_state='failed',
                    completed_at=CURRENT_TIMESTAMP,
                    error_type=?,
                    error_message=?
                WHERE attempt_id=?
                """,
                (
                    error_type,
                    error_message,
                    claim.attempt_id,
                ),
            )

            conn.commit()

        return {
            "retry_exhausted": exhausted,
            "queue_state": "failed" if exhausted else "queued",
            "message": (
                "retry limit exhausted"
                if exhausted
                else "failure recorded; object returned to queue"
            ),
            "error_type": error_type,
            "error": error_message,
        }

    @staticmethod
    def _validate_source_path(path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(
                f"Source document does not exist: {path}"
            )

        if not path.is_file():
            raise RuntimeError(
                f"Source document is not a regular file: {path}"
            )

    @staticmethod
    def _abandon_processing_attempts(
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
    ) -> None:
        conn.execute(
            """
            UPDATE knowledge_assimilation_attempts
            SET attempt_state='abandoned',
                completed_at=CURRENT_TIMESTAMP,
                error_type='StaleProcessingRecovery',
                error_message='Recovered stale processing claim'
            WHERE object_uuid=?
              AND attempt_state='processing'
            """,
            (object_uuid,),
        )

    @staticmethod
    def _fail_processing_attempts_as_stale_exhausted(
        *,
        conn: sqlite3.Connection,
        object_uuid: str,
    ) -> None:
        conn.execute(
            """
            UPDATE knowledge_assimilation_attempts
            SET attempt_state='failed',
                completed_at=CURRENT_TIMESTAMP,
                error_type='StaleProcessingRetryExhausted',
                error_message=(
                    'Stale processing claim exhausted retry limit'
                )
            WHERE object_uuid=?
              AND attempt_state='processing'
            """,
            (object_uuid,),
        )
