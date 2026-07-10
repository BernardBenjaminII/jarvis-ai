from __future__ import annotations

import json
import re
from pathlib import Path

from knowledge_engine.integrity.models import (
    IntegrityIssue,
    IntegrityReport,
)
from knowledge_engine.storage.database import KnowledgeDatabase


TUPLE_FRAGMENT_PATTERNS = (
    re.compile(r"\(\s*['\"][^'\"]+['\"]\s*,\s*\d+\s*,"),
    re.compile(r"['\"]\s*,\s*\d+\s*,\s*['\"]"),
    re.compile(r"\.pdf['\"]\s*,\s*\d+\s*,"),
)

EMPTY_TUPLE_TEXT_PATTERN = re.compile(
    r"\(\s*['\"][^'\"]+['\"]\s*,\s*\d+\s*,\s*['\"]{2}\s*\)"
)


class KnowledgeIntegrityAuditor:
    """
    Read-only auditor for Knowledge Engine persistence.

    It examines:

        document_text
            ↓
        document_chunks
            ↓
        chunk_embeddings

    The auditor reports malformed text, tuple serialization,
    missing records, invalid embedding JSON, and dimensional mismatch.
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db = KnowledgeDatabase(self.db_path)

    def run(
        self,
        *,
        document_limit: int = 100,
        chunk_limit: int = 500,
    ) -> IntegrityReport:
        report = IntegrityReport(
            database_path=str(self.db_path),
        )

        if not self.db_path.exists():
            report.issues.append(
                IntegrityIssue(
                    stage="database",
                    severity="error",
                    message="Knowledge database does not exist.",
                    file_path=str(self.db_path),
                )
            )
            return report

        try:
            with self.db.connect() as conn:
                tables = self._table_names(conn)

                report.details["tables"] = sorted(tables)

                self._audit_document_text(
                    conn,
                    report,
                    tables,
                    document_limit,
                )

                self._audit_chunks(
                    conn,
                    report,
                    tables,
                    chunk_limit,
                )

                self._audit_embeddings(
                    conn,
                    report,
                    tables,
                    chunk_limit,
                )

        except Exception as exc:
            report.issues.append(
                IntegrityIssue(
                    stage="database",
                    severity="error",
                    message=f"Integrity audit failed: {exc}",
                    file_path=str(self.db_path),
                )
            )

        return report

    def _table_names(self, conn) -> set[str]:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        ).fetchall()

        return {row["name"] for row in rows}

    def _audit_document_text(
        self,
        conn,
        report: IntegrityReport,
        tables: set[str],
        limit: int,
    ) -> None:
        if "document_text" not in tables:
            report.issues.append(
                IntegrityIssue(
                    stage="document_text",
                    severity="error",
                    message="Missing document_text table.",
                )
            )
            return

        rows = conn.execute(
            """
            SELECT file_path,
                   text,
                   status,
                   content_chars
            FROM document_text
            ORDER BY file_path
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        report.documents_checked = len(rows)

        for row in rows:
            file_path = row["file_path"] or ""
            text = row["text"] or ""
            status = row["status"] or ""
            content_chars = row["content_chars"] or 0

            if status == "processed" and not text.strip():
                self._add_issue(
                    report,
                    stage="document_text",
                    severity="error",
                    message="Processed document contains no text.",
                    file_path=file_path,
                    preview=text,
                )

            if content_chars != len(text):
                self._add_issue(
                    report,
                    stage="document_text",
                    severity="warning",
                    message=(
                        "content_chars does not match actual text length: "
                        f"stored={content_chars}, actual={len(text)}"
                    ),
                    file_path=file_path,
                    preview=text,
                )

            self._check_serialized_tuple(
                report,
                stage="document_text",
                file_path=file_path,
                record_id=file_path,
                text=text,
            )

    def _audit_chunks(
        self,
        conn,
        report: IntegrityReport,
        tables: set[str],
        limit: int,
    ) -> None:
        if "document_chunks" not in tables:
            report.issues.append(
                IntegrityIssue(
                    stage="document_chunks",
                    severity="error",
                    message="Missing document_chunks table.",
                )
            )
            return

        rows = conn.execute(
            """
            SELECT chunk_uuid,
                   file_path,
                   chunk_index,
                   text,
                   char_count,
                   checksum
            FROM document_chunks
            ORDER BY file_path, chunk_index
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        report.chunks_checked = len(rows)

        for row in rows:
            chunk_uuid = row["chunk_uuid"] or ""
            file_path = row["file_path"] or ""
            text = row["text"] or ""
            char_count = row["char_count"] or 0

            if not text.strip():
                self._add_issue(
                    report,
                    stage="document_chunks",
                    severity="error",
                    message="Chunk contains no text.",
                    file_path=file_path,
                    record_id=chunk_uuid,
                    preview=text,
                )

            if char_count != len(text):
                self._add_issue(
                    report,
                    stage="document_chunks",
                    severity="warning",
                    message=(
                        "char_count does not match actual chunk length: "
                        f"stored={char_count}, actual={len(text)}"
                    ),
                    file_path=file_path,
                    record_id=chunk_uuid,
                    preview=text,
                )

            if len(text.strip()) < 20:
                self._add_issue(
                    report,
                    stage="document_chunks",
                    severity="warning",
                    message="Chunk is unusually small.",
                    file_path=file_path,
                    record_id=chunk_uuid,
                    preview=text,
                )

            self._check_serialized_tuple(
                report,
                stage="document_chunks",
                file_path=file_path,
                record_id=chunk_uuid,
                text=text,
            )

    def _audit_embeddings(
        self,
        conn,
        report: IntegrityReport,
        tables: set[str],
        limit: int,
    ) -> None:
        if "chunk_embeddings" not in tables:
            report.issues.append(
                IntegrityIssue(
                    stage="chunk_embeddings",
                    severity="error",
                    message="Missing chunk_embeddings table.",
                )
            )
            return

        rows = conn.execute(
            """
            SELECT chunk_uuid,
                   vector_json,
                   dimensions
            FROM chunk_embeddings
            ORDER BY chunk_uuid
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        report.embeddings_checked = len(rows)

        for row in rows:
            chunk_uuid = row["chunk_uuid"] or ""
            vector_json = row["vector_json"] or ""
            dimensions = row["dimensions"] or 0

            try:
                vector = json.loads(vector_json)
            except Exception as exc:
                self._add_issue(
                    report,
                    stage="chunk_embeddings",
                    severity="error",
                    message=f"Invalid embedding JSON: {exc}",
                    record_id=chunk_uuid,
                    preview=vector_json,
                )
                continue

            if not isinstance(vector, list):
                self._add_issue(
                    report,
                    stage="chunk_embeddings",
                    severity="error",
                    message="Embedding vector is not a list.",
                    record_id=chunk_uuid,
                    preview=repr(vector),
                )
                continue

            if dimensions != len(vector):
                self._add_issue(
                    report,
                    stage="chunk_embeddings",
                    severity="error",
                    message=(
                        "Embedding dimension mismatch: "
                        f"stored={dimensions}, actual={len(vector)}"
                    ),
                    record_id=chunk_uuid,
                )

            if not vector:
                self._add_issue(
                    report,
                    stage="chunk_embeddings",
                    severity="error",
                    message="Embedding vector is empty.",
                    record_id=chunk_uuid,
                )

    def _check_serialized_tuple(
        self,
        report: IntegrityReport,
        *,
        stage: str,
        file_path: str,
        record_id: str,
        text: str,
    ) -> None:
        if not text:
            return

        if EMPTY_TUPLE_TEXT_PATTERN.search(text):
            self._add_issue(
                report,
                stage=stage,
                severity="error",
                message="Serialized extraction tuple with empty text detected.",
                file_path=file_path,
                record_id=record_id,
                preview=text,
            )
            return

        matches = sum(
            1
            for pattern in TUPLE_FRAGMENT_PATTERNS
            if pattern.search(text)
        )

        if matches:
            self._add_issue(
                report,
                stage=stage,
                severity="error",
                message="Possible serialized extraction tuple detected.",
                file_path=file_path,
                record_id=record_id,
                preview=text,
            )

    def _add_issue(
        self,
        report: IntegrityReport,
        *,
        stage: str,
        severity: str,
        message: str,
        file_path: str = "",
        record_id: str = "",
        preview: str = "",
    ) -> None:
        cleaned_preview = (
            preview
            .replace("\r", " ")
            .replace("\n", " ")
            .strip()
        )

        report.issues.append(
            IntegrityIssue(
                stage=stage,
                severity=severity,
                message=message,
                file_path=file_path,
                record_id=record_id,
                preview=cleaned_preview[:300],
            )
        )
