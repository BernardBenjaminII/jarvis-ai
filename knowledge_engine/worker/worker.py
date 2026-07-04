from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from knowledge_engine.worker.extraction import checksum_text, extract_text


class KnowledgeWorker:
    def __init__(self, db):
        self.db = db

    def run_once(self) -> dict:
        with self.db.connect() as conn:
            row = conn.execute(
                """
                SELECT object_uuid, object_path, object_type
                FROM knowledge_assimilation_queue
                WHERE queue_state='queued'
                ORDER BY priority DESC, queued_at ASC
                LIMIT 1
                """
            ).fetchone()

            if row is None:
                return {"processed": 0, "message": "no queued work found"}

            object_uuid = row["object_uuid"]
            object_path = row["object_path"]
            object_type = row["object_type"]

            if object_type != "single_document":
                return self._defer_unsupported(conn, object_uuid, object_path, object_type)

            return self._process_single_document(conn, object_uuid, object_path, object_type)

    def _process_single_document(self, conn, object_uuid: str, object_path: str, object_type: str) -> dict:
        original_path = Path(object_path)

        if not original_path.exists():
            return self._fail(conn, object_uuid, object_path, "path does not exist")

        resolved_path = self._resolve_primary_file(original_path)

        if resolved_path is None:
            return self._fail(conn, object_uuid, object_path, "no processable file found")

        timestamp = datetime.now(timezone.utc).isoformat()
        stat = resolved_path.stat()
        sha256 = self._sha256_file(resolved_path)

        self._mark_processing(conn, object_uuid)

        conn.execute(
            """
            INSERT INTO catalog_documents(
                file_path, sha256, title, file_type, size_bytes,
                source_name, collection_id, created_at, updated_at,
                detected_type, inspection_reason, readable, content_chars
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(file_path)
            DO UPDATE SET
                sha256=excluded.sha256,
                title=excluded.title,
                file_type=excluded.file_type,
                size_bytes=excluded.size_bytes,
                updated_at=excluded.updated_at,
                detected_type=excluded.detected_type,
                inspection_reason=excluded.inspection_reason,
                readable=excluded.readable,
                content_chars=excluded.content_chars
            """,
            (
                str(resolved_path), sha256, resolved_path.stem,
                resolved_path.suffix.lstrip("."), stat.st_size,
                "knowledge_worker", None, timestamp, timestamp,
                resolved_path.suffix.lstrip("."), f"knowledge_object:{object_type}",
                1, 0,
            ),
        )

        text, extractor, extraction_status, extraction_error = extract_text(resolved_path)
        text_checksum = checksum_text(text)
        content_chars = len(text)

        conn.execute(
            """
            INSERT INTO document_text(
                file_path, text, extractor, content_chars, checksum,
                status, error, extracted_at
            )
            VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(file_path)
            DO UPDATE SET
                text=excluded.text,
                extractor=excluded.extractor,
                content_chars=excluded.content_chars,
                checksum=excluded.checksum,
                status=excluded.status,
                error=excluded.error,
                extracted_at=excluded.extracted_at
            """,
            (
                str(resolved_path), text, extractor, content_chars,
                text_checksum, extraction_status, extraction_error, timestamp,
            ),
        )

        conn.execute(
            """
            INSERT INTO document_assimilation(
                file_path, sha256, title, domain, discipline, subject,
                collection_id, confidence, evidence_json, content_chars,
                assigned_by, updated_at
            )
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(file_path)
            DO UPDATE SET
                sha256=excluded.sha256,
                title=excluded.title,
                domain=excluded.domain,
                discipline=excluded.discipline,
                subject=excluded.subject,
                confidence=excluded.confidence,
                evidence_json=excluded.evidence_json,
                content_chars=excluded.content_chars,
                assigned_by=excluded.assigned_by,
                updated_at=excluded.updated_at
            """,
            (
                str(resolved_path), sha256, resolved_path.stem,
                None, None, object_type, None, 1.0, "{}",
                content_chars, "knowledge_worker_v2", timestamp,
            ),
        )

        conn.execute(
            """
            UPDATE catalog_documents
            SET content_chars=?, readable=?
            WHERE file_path=?
            """,
            (content_chars, 1 if content_chars > 0 else 0, str(resolved_path)),
        )

        conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='completed',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        if extraction_status == "processed" and content_chars > 0:
            lifecycle_state = "extracted"
            assimilation_state = "ready_for_chunking"
            final_status = "ready_for_chunking"
        else:
            lifecycle_state = "extraction_failed"
            assimilation_state = "needs_review"
            final_status = "needs_review"

        conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state=?,
                assimilation_state=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (lifecycle_state, assimilation_state, object_uuid),
        )

        conn.commit()

        return {
            "processed": 1,
            "object_uuid": object_uuid,
            "object_type": object_type,
            "object_path": object_path,
            "resolved_file": str(resolved_path),
            "extractor": extractor,
            "extraction_status": extraction_status,
            "extraction_error": extraction_error,
            "content_chars": content_chars,
            "status": final_status,
        }

    def _resolve_primary_file(self, path: Path) -> Path | None:
        if path.is_file():
            return path

        if not path.is_dir():
            return None

        preferred_extensions = [".pdf", ".epub", ".docx", ".md", ".txt", ".rtf"]

        files = [
            p for p in path.rglob("*")
            if p.is_file() and not self._is_ignored_path(p)
        ]

        if not files:
            return None

        for ext in preferred_extensions:
            matches = sorted(
                [p for p in files if p.suffix.lower() == ext],
                key=lambda p: (len(p.parts), str(p).lower()),
            )
            if matches:
                return matches[0]

        return sorted(files, key=lambda p: (len(p.parts), str(p).lower()))[0]

    def _is_ignored_path(self, path: Path) -> bool:
        ignored_parts = {
            ".git", ".venv", "venv", "__pycache__", ".idea",
            ".vscode", "node_modules", "site-packages",
        }
        return bool(set(path.parts) & ignored_parts)

    def _sha256_file(self, path: Path, chunk_size: int = 1024 * 1024) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(chunk_size):
                digest.update(chunk)
        return digest.hexdigest()

    def _mark_processing(self, conn, object_uuid: str) -> None:
        conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='processing',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='processing',
                assimilation_state='processing',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

    def _defer_unsupported(self, conn, object_uuid: str, object_path: str, object_type: str) -> dict:
        conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='deferred',
                reason='unsupported object type for current worker',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='deferred',
                assimilation_state='deferred',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        conn.commit()

        return {
            "processed": 0,
            "deferred": 1,
            "object_uuid": object_uuid,
            "object_type": object_type,
            "object_path": object_path,
        }

    def _fail(self, conn, object_uuid: str, object_path: str, reason: str) -> dict:
        conn.execute(
            """
            UPDATE knowledge_assimilation_queue
            SET queue_state='failed',
                reason=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (reason, object_uuid),
        )

        conn.execute(
            """
            UPDATE knowledge_registry
            SET lifecycle_state='failed',
                assimilation_state='failed',
                updated_at=CURRENT_TIMESTAMP
            WHERE object_uuid=?
            """,
            (object_uuid,),
        )

        conn.commit()

        return {
            "processed": 0,
            "failed": 1,
            "object_uuid": object_uuid,
            "object_path": object_path,
            "reason": reason,
        }
