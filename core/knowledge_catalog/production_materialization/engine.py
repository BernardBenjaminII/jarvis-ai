from __future__ import annotations

import concurrent.futures
import hashlib
import mimetypes
import sqlite3
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from core.knowledge_catalog.materialization import (
    chunk_text,
    extract_text,
)

from .checkpoint import CheckpointStore
from .models import (
    Artifact,
    EngineConfig,
    MaterializationStage,
    Result,
)
from .reliability import (
    ReliableSQLite,
    SQLiteReliabilityPolicy,
    is_transient_lock_error,
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(text: str) -> str:
    return hashlib.sha256(
        text.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()


class ProductionMaterializationEngine:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.store = CheckpointStore(
            config.checkpoint_db
        )
        self.sqlite = ReliableSQLite(
            config.runtime_catalog,
            SQLiteReliabilityPolicy(),
        )
        self.database_configuration = (
            self.sqlite.configure_runtime_database()
        )
        self.recovered_incomplete = (
            self.store.recover_incomplete_states()
        )
        self.recovered_lock_failures = (
            self.store.recover_transient_lock_failures()
        )

    def catalog_counts(self) -> dict[str, int]:
        connection = self.sqlite.connect(
            read_only=True
        )

        try:
            return {
                table: int(
                    connection.execute(
                        f'SELECT COUNT(*) FROM "{table}"'
                    ).fetchone()[0]
                )
                for table in (
                    "runtime_documents",
                    "runtime_chunks",
                    "runtime_chunks_fts",
                )
            }
        finally:
            connection.close()

    def extract_one(self, item) -> Artifact:
        self.store.set_stage(
            item.candidate_id,
            MaterializationStage.EXTRACTING,
            "Extraction started.",
            attempt=True,
        )
        started = time.monotonic()
        text = str(
            extract_text(Path(item.path))
            or ""
        )

        if not text.strip():
            raise ValueError(
                "Extractor produced no usable text."
            )

        chunks = []

        for index, (
            start,
            end,
            value,
        ) in enumerate(
            chunk_text(
                text,
                target_chars=(
                    self.config.target_chunk_chars
                ),
                overlap_chars=(
                    self.config.overlap_chars
                ),
                minimum_chars=(
                    self.config.minimum_chunk_chars
                ),
            )
        ):
            chunks.append(
                {
                    "chunk_index": index,
                    "chunk_text": value,
                    "start_char": int(start),
                    "end_char": int(end),
                    "token_estimate": max(
                        1,
                        len(value) // 4,
                    ),
                    "content_sha256": digest(
                        value
                    ),
                }
            )

        if not chunks:
            raise ValueError(
                "Chunker produced no chunks."
            )

        elapsed = time.monotonic() - started

        self.store.set_stage(
            item.candidate_id,
            MaterializationStage.CHUNKED,
            f"Produced {len(chunks)} chunks.",
            extraction_seconds=elapsed,
        )

        return Artifact(
            candidate_id=item.candidate_id,
            path=item.path,
            title=item.title,
            category=item.category,
            sha256=(
                item.sha256
                or digest(text)
            ),
            media_type=(
                mimetypes.guess_type(
                    item.path
                )[0]
                or "application/octet-stream"
            ),
            content_text=text,
            chunks=tuple(chunks),
            extraction_seconds=elapsed,
        )

    def _write_transaction(self, artifact):
        connection = self.sqlite.connect()

        try:
            connection.execute(
                "BEGIN IMMEDIATE"
            )

            if connection.execute(
                """
                SELECT 1
                FROM runtime_documents
                WHERE file_path=?
                """,
                (artifact.path,),
            ).fetchone():
                connection.rollback()

                return {
                    "already_present": True,
                    "document_delta": 0,
                    "chunk_delta": 0,
                    "fts_delta": 0,
                }

            cursor = connection.execute(
                """
                INSERT INTO runtime_documents(
                    file_path,
                    sha256,
                    title,
                    media_type,
                    content_text,
                    content_chars
                )
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact.path,
                    artifact.sha256,
                    artifact.title,
                    artifact.media_type,
                    artifact.content_text,
                    len(artifact.content_text),
                ),
            )
            document_id = int(
                cursor.lastrowid
            )

            chunk_count = 0

            for chunk in artifact.chunks:
                chunk_cursor = connection.execute(
                    """
                    INSERT INTO runtime_chunks(
                        document_id,
                        chunk_index,
                        chunk_text,
                        start_char,
                        end_char,
                        token_estimate,
                        content_sha256
                    )
                    VALUES(?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        chunk["chunk_index"],
                        chunk["chunk_text"],
                        chunk["start_char"],
                        chunk["end_char"],
                        chunk["token_estimate"],
                        chunk["content_sha256"],
                    ),
                )
                chunk_id = int(
                    chunk_cursor.lastrowid
                )

                connection.execute(
                    """
                    INSERT INTO runtime_chunks_fts(
                        chunk_text,
                        title,
                        file_path,
                        document_id,
                        chunk_id
                    )
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        chunk["chunk_text"],
                        artifact.title,
                        artifact.path,
                        str(document_id),
                        str(chunk_id),
                    ),
                )
                chunk_count += 1

            connection.commit()

            return {
                "already_present": False,
                "document_delta": 1,
                "chunk_delta": chunk_count,
                "fts_delta": chunk_count,
            }
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def write_one(self, artifact) -> Result:
        started = time.monotonic()
        retry_events = []

        def on_retry(attempt, delay, exc):
            retry_events.append(
                {
                    "attempt": attempt,
                    "delay": delay,
                    "error": str(exc),
                }
            )

        try:
            result = self.sqlite.run_with_retry(
                lambda: self._write_transaction(
                    artifact
                ),
                on_retry=on_retry,
            )
        except Exception as exc:
            detail = (
                f"{type(exc).__name__}: {exc}"
            )

            if is_transient_lock_error(exc):
                detail += (
                    " | SQLite lock retries exhausted."
                )

            self.store.set_stage(
                artifact.candidate_id,
                MaterializationStage.FAILED,
                detail,
                write_seconds=(
                    time.monotonic() - started
                ),
            )

            return Result(
                candidate_id=artifact.candidate_id,
                path=artifact.path,
                stage=MaterializationStage.FAILED,
                detail=detail,
                extraction_seconds=(
                    artifact.extraction_seconds
                ),
                write_seconds=(
                    time.monotonic() - started
                ),
            )

        write_seconds = time.monotonic() - started

        if result["already_present"]:
            stage = MaterializationStage.SKIPPED
            detail = "Already present."
        elif (
            result["document_delta"] == 1
            and result["chunk_delta"] > 0
            and result["chunk_delta"]
            == result["fts_delta"]
        ):
            stage = MaterializationStage.COMPLETE
            detail = (
                f"Committed "
                f"{result['chunk_delta']} chunks."
            )
        elif (
            result["chunk_delta"]
            != result["fts_delta"]
        ):
            stage = (
                MaterializationStage.QUARANTINED
            )
            detail = (
                "Chunk/FTS mismatch "
                f"{result['chunk_delta']}/"
                f"{result['fts_delta']}."
            )
        else:
            stage = MaterializationStage.FAILED
            detail = "Unexpected write deltas."

        if retry_events:
            detail += (
                f" Lock retries: {len(retry_events)}."
            )

        self.store.set_stage(
            artifact.candidate_id,
            stage,
            detail,
            write_seconds=write_seconds,
        )

        return Result(
            candidate_id=artifact.candidate_id,
            path=artifact.path,
            stage=stage,
            detail=detail,
            document_delta=int(
                result["document_delta"]
            ),
            chunk_delta=int(
                result["chunk_delta"]
            ),
            fts_delta=int(
                result["fts_delta"]
            ),
            extraction_seconds=(
                artifact.extraction_seconds
            ),
            write_seconds=write_seconds,
        )

    def run(self):
        run_id = (
            "X-A1.1-"
            + uuid.uuid4().hex[:12]
        )
        started_at = now()
        started = time.monotonic()
        pre = self.catalog_counts()
        items = self.store.next_items(
            self.config.batch_size,
            self.config.retry_failures,
        )
        results = []

        if self.config.dry_run:
            for item in items:
                self.store.set_stage(
                    item.candidate_id,
                    MaterializationStage.VALIDATED,
                    "Dry-run validated.",
                )
                results.append(
                    Result(
                        item.candidate_id,
                        item.path,
                        MaterializationStage.VALIDATED,
                        "Dry-run validated.",
                    )
                )
        else:
            stop_requested = False

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.workers
            ) as executor:
                futures = {
                    executor.submit(
                        self.extract_one,
                        item,
                    ): item
                    for item in items
                }

                for future in concurrent.futures.as_completed(
                    futures
                ):
                    item = futures[future]

                    if stop_requested:
                        if future.cancel():
                            self.store.set_stage(
                                item.candidate_id,
                                MaterializationStage.VALIDATED,
                                "Cancelled after stop-on-error; safe to resume.",
                            )
                            continue

                    try:
                        artifact = future.result()
                    except Exception as exc:
                        detail = (
                            f"{type(exc).__name__}: {exc}"
                        )
                        self.store.set_stage(
                            item.candidate_id,
                            MaterializationStage.FAILED,
                            detail,
                        )
                        results.append(
                            Result(
                                item.candidate_id,
                                item.path,
                                MaterializationStage.FAILED,
                                detail,
                            )
                        )
                        if self.config.stop_on_error:
                            stop_requested = True
                    else:
                        if stop_requested:
                            self.store.set_stage(
                                item.candidate_id,
                                MaterializationStage.VALIDATED,
                                "Extraction completed after stop request; reset for safe resume.",
                            )
                            continue

                        result = self.write_one(
                            artifact
                        )
                        results.append(result)

                        if self.config.throttle_seconds:
                            time.sleep(
                                self.config.throttle_seconds
                            )

                        if (
                            self.config.stop_on_error
                            and result.stage
                            in {
                                MaterializationStage.FAILED,
                                MaterializationStage.QUARANTINED,
                            }
                        ):
                            stop_requested = True

                if stop_requested:
                    for future, item in futures.items():
                        if not future.done():
                            future.cancel()
                            self.store.set_stage(
                                item.candidate_id,
                                MaterializationStage.VALIDATED,
                                "Cancelled after stop-on-error; safe to resume.",
                            )

        post = self.catalog_counts()
        elapsed = max(
            0.000001,
            time.monotonic() - started,
        )
        completed = sum(
            result.stage
            in {
                MaterializationStage.COMPLETE,
                MaterializationStage.SKIPPED,
                MaterializationStage.VALIDATED,
            }
            for result in results
        )
        stage_counts = dict(
            Counter(
                result.stage.value
                for result in results
            )
        )
        documents_per_minute = (
            completed / elapsed * 60.0
        )
        chunks_added = (
            post["runtime_chunks"]
            - pre["runtime_chunks"]
        )
        chunks_per_minute = (
            chunks_added / elapsed * 60.0
        )
        remaining = self.store.pending()
        eta = (
            None
            if documents_per_minute <= 0
            else (
                remaining
                / documents_per_minute
                * 60.0
            )
        )
        failed = sum(
            stage_counts.get(name, 0)
            for name in (
                MaterializationStage.FAILED.value,
                MaterializationStage.QUARANTINED.value,
            )
        )

        if self.config.dry_run:
            classification = (
                "SQLITE_RELIABILITY_DRY_RUN_READY"
            )
            status = "EXCELLENT"
        elif (
            post["runtime_chunks"]
            != post["runtime_chunks_fts"]
        ):
            classification = (
                "SQLITE_RELIABILITY_FTS_INTEGRITY_FAILURE"
            )
            status = "FAILED"
        elif failed:
            classification = (
                "SQLITE_RELIABILITY_COMPLETED_WITH_FAILURES"
            )
            status = "FAILED"
        else:
            classification = (
                "SQLITE_RELIABILITY_BATCH_COMPLETED"
            )
            status = "EXCELLENT"

        return {
            "run_id": run_id,
            "status": status,
            "classification": classification,
            "dry_run": self.config.dry_run,
            "started_at": started_at,
            "completed_at": now(),
            "elapsed_seconds": elapsed,
            "workers": self.config.workers,
            "candidates_selected": len(items),
            "candidates_completed": completed,
            "stage_counts": stage_counts,
            "pre_counts": pre,
            "post_counts": post,
            "documents_per_minute": documents_per_minute,
            "chunks_per_minute": chunks_per_minute,
            "estimated_remaining_seconds": eta,
            "checkpoint_db": str(
                self.config.checkpoint_db.resolve()
            ),
            "database_configuration": (
                self.database_configuration
            ),
            "recovered_incomplete": (
                self.recovered_incomplete
            ),
            "recovered_lock_failures": (
                self.recovered_lock_failures
            ),
            "results": [
                result.to_dict()
                for result in results
            ],
        }
