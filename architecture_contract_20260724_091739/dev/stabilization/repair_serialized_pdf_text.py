from __future__ import annotations

import argparse
import hashlib
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from knowledge_engine.chunking.chunker import DocumentChunker
from knowledge_engine.integrity.auditor import (
    EMPTY_TUPLE_TEXT_PATTERN,
    TUPLE_FRAGMENT_PATTERNS,
    KnowledgeIntegrityAuditor,
)
from knowledge_engine.processors.registry import default_registry
from knowledge_engine.storage.database import KnowledgeDatabase


DEFAULT_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

DEFAULT_BACKUP_DIR = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/backups"
)


@dataclass
class RepairCandidate:
    file_path: Path
    issue_count: int
    issue_messages: list[str]


@dataclass
class PreparedRepair:
    file_path: Path
    processor: str
    status: str
    error: str | None
    text: str
    chunk_strategy: str
    chunks: list[dict]


@dataclass
class RepairOutcome:
    file_path: Path
    repaired: bool
    status: str
    characters: int = 0
    chunks_rebuilt: int = 0
    embeddings_removed: int = 0
    error: str | None = None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def text_checksum(text: str) -> str:
    return hashlib.sha256(
        text.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()


def table_exists(
    conn: sqlite3.Connection,
    table_name: str,
) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def table_columns(
    conn: sqlite3.Connection,
    table_name: str,
) -> set[str]:
    if not table_exists(conn, table_name):
        return set()

    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return {
        row["name"]
        for row in rows
    }


def contains_serialized_tuple(text: str) -> bool:
    if not text:
        return False

    if EMPTY_TUPLE_TEXT_PATTERN.search(text):
        return True

    return any(
        pattern.search(text)
        for pattern in TUPLE_FRAGMENT_PATTERNS
    )


def create_database_backup(
    database_path: Path,
    backup_directory: Path,
) -> Path:
    backup_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup_path = (
        backup_directory
        / f"{database_path.stem}.before_pdf_repair.{timestamp}.sqlite"
    )

    source = sqlite3.connect(database_path)
    destination = sqlite3.connect(backup_path)

    try:
        source.backup(destination)
        destination.commit()

    finally:
        destination.close()
        source.close()

    return backup_path


def discover_candidates(
    database_path: Path,
    document_limit: int,
) -> list[RepairCandidate]:
    auditor = KnowledgeIntegrityAuditor(
        database_path
    )

    report = auditor.run(
        document_limit=document_limit,
        chunk_limit=1,
    )

    grouped: dict[str, list[str]] = {}

    for issue in report.issues:
        if issue.stage != "document_text":
            continue

        if issue.severity != "error":
            continue

        if "tuple" not in issue.message.lower():
            continue

        if not issue.file_path:
            continue

        grouped.setdefault(
            issue.file_path,
            [],
        ).append(issue.message)

    return [
        RepairCandidate(
            file_path=Path(file_path),
            issue_count=len(messages),
            issue_messages=sorted(
                set(messages)
            ),
        )
        for file_path, messages in sorted(
            grouped.items()
        )
    ]


def make_chunk_record(
    file_path: Path,
    chunk_index: int,
    text: str,
    chunk_type: str,
) -> dict:
    checksum = text_checksum(text)

    chunk_uuid = str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{file_path}:{chunk_index}:{checksum}",
        )
    )

    return {
        "chunk_uuid": chunk_uuid,
        "file_path": str(file_path),
        "chunk_index": chunk_index,
        "chunk_type": chunk_type,
        "heading": None,
        "text": text,
        "char_count": len(text),
        "checksum": checksum,
        "embedding_state": "not_embedded",
    }


def prepare_repair(
    file_path: Path,
) -> PreparedRepair:
    if not file_path.exists():
        raise FileNotFoundError(
            f"Source file does not exist: {file_path}"
        )

    if not file_path.is_file():
        raise ValueError(
            f"Source path is not a file: {file_path}"
        )

    processor = default_registry().get(
        file_path
    )

    if processor is None:
        raise RuntimeError(
            "No processor supports "
            f"{file_path.suffix or file_path.name}"
        )

    result = processor.process(
        file_path
    )

    if result.status == "failed":
        raise RuntimeError(
            result.error
            or "Document processing failed."
        )

    clean_text = result.text or ""

    if contains_serialized_tuple(
        clean_text
    ):
        raise RuntimeError(
            "Reprocessed output still contains "
            "serialized extraction tuples."
        )

    chunker = DocumentChunker()

    chunk_result = chunker.chunk(
        clean_text,
        file_path=str(file_path),
    )

    chunks = [
        make_chunk_record(
            file_path=file_path,
            chunk_index=index,
            text=chunk_text,
            chunk_type=chunk_result.strategy,
        )
        for index, chunk_text in enumerate(
            chunk_result.chunks
        )
        if chunk_text.strip()
    ]

    return PreparedRepair(
        file_path=file_path,
        processor=result.processor,
        status=result.status,
        error=result.error,
        text=clean_text,
        chunk_strategy=chunk_result.strategy,
        chunks=chunks,
    )


def update_document_text(
    conn: sqlite3.Connection,
    repair: PreparedRepair,
) -> None:
    columns = table_columns(
        conn,
        "document_text",
    )

    if not columns:
        raise RuntimeError(
            "Missing document_text table."
        )

    values = {
        "text": repair.text,
        "processor": repair.processor,
        "status": repair.status,
        "error": repair.error,
        "content_chars": len(repair.text),
        "checksum": text_checksum(
            repair.text
        ),
        "updated_at": utc_now(),
    }

    assignments: list[str] = []
    parameters: list[object] = []

    for column, value in values.items():
        if column not in columns:
            continue

        assignments.append(
            f"{column}=?"
        )

        parameters.append(value)

    if not assignments:
        raise RuntimeError(
            "No supported document_text columns "
            "were found for update."
        )

    parameters.append(
        str(repair.file_path)
    )

    cursor = conn.execute(
        f"""
        UPDATE document_text
        SET {", ".join(assignments)}
        WHERE file_path=?
        """,
        parameters,
    )

    if cursor.rowcount != 1:
        raise RuntimeError(
            "Expected one document_text row for "
            f"{repair.file_path}; updated {cursor.rowcount}."
        )


def remove_existing_embeddings(
    conn: sqlite3.Connection,
    file_path: Path,
) -> int:
    if not table_exists(
        conn,
        "document_chunks",
    ):
        return 0

    if not table_exists(
        conn,
        "chunk_embeddings",
    ):
        return 0

    rows = conn.execute(
        """
        SELECT chunk_uuid
        FROM document_chunks
        WHERE file_path=?
        """,
        (str(file_path),),
    ).fetchall()

    chunk_uuids = [
        row["chunk_uuid"]
        for row in rows
    ]

    if not chunk_uuids:
        return 0

    placeholders = ",".join(
        "?"
        for _ in chunk_uuids
    )

    cursor = conn.execute(
        f"""
        DELETE FROM chunk_embeddings
        WHERE chunk_uuid IN ({placeholders})
        """,
        chunk_uuids,
    )

    return max(
        cursor.rowcount,
        0,
    )


def replace_document_chunks(
    conn: sqlite3.Connection,
    repair: PreparedRepair,
) -> int:
    columns = table_columns(
        conn,
        "document_chunks",
    )

    if not columns:
        raise RuntimeError(
            "Missing document_chunks table."
        )

    conn.execute(
        """
        DELETE FROM document_chunks
        WHERE file_path=?
        """,
        (str(repair.file_path),),
    )

    if not repair.chunks:
        return 0

    supported_columns = [
        column
        for column in (
            "chunk_uuid",
            "file_path",
            "chunk_index",
            "chunk_type",
            "heading",
            "text",
            "char_count",
            "checksum",
            "embedding_state",
        )
        if column in columns
    ]

    required_columns = {
        "chunk_uuid",
        "file_path",
        "chunk_index",
        "text",
    }

    missing_required = (
        required_columns
        - set(supported_columns)
    )

    if missing_required:
        raise RuntimeError(
            "document_chunks is missing required columns: "
            + ", ".join(
                sorted(missing_required)
            )
        )

    column_sql = ", ".join(
        supported_columns
    )

    placeholder_sql = ", ".join(
        "?"
        for _ in supported_columns
    )

    rows = [
        tuple(
            chunk[column]
            for column in supported_columns
        )
        for chunk in repair.chunks
    ]

    conn.executemany(
        f"""
        INSERT INTO document_chunks
            ({column_sql})
        VALUES
            ({placeholder_sql})
        """,
        rows,
    )

    return len(rows)


def update_registry_state(
    conn: sqlite3.Connection,
    repair: PreparedRepair,
) -> None:
    columns = table_columns(
        conn,
        "knowledge_registry",
    )

    if not columns:
        return

    values: dict[str, object] = {}

    if repair.text.strip():
        values.update(
            {
                "lifecycle_state": "chunked",
                "assimilation_state": (
                    "ready_for_embedding"
                ),
            }
        )

    else:
        values.update(
            {
                "lifecycle_state": "extracted",
                "assimilation_state": (
                    "needs_review"
                ),
            }
        )

    values["updated_at"] = utc_now()

    assignments: list[str] = []
    parameters: list[object] = []

    for column, value in values.items():
        if column not in columns:
            continue

        assignments.append(
            f"{column}=?"
        )

        parameters.append(value)

    if not assignments:
        return

    parameters.append(
        str(repair.file_path)
    )

    conn.execute(
        f"""
        UPDATE knowledge_registry
        SET {", ".join(assignments)}
        WHERE object_path=?
        """,
        parameters,
    )


def apply_repair(
    database_path: Path,
    repair: PreparedRepair,
) -> RepairOutcome:
    database = KnowledgeDatabase(
        database_path
    )

    try:
        with database.connect() as conn:
            conn.execute(
                "BEGIN IMMEDIATE"
            )

            embeddings_removed = (
                remove_existing_embeddings(
                    conn,
                    repair.file_path,
                )
            )

            update_document_text(
                conn,
                repair,
            )

            chunks_rebuilt = (
                replace_document_chunks(
                    conn,
                    repair,
                )
            )

            update_registry_state(
                conn,
                repair,
            )

            conn.commit()

        return RepairOutcome(
            file_path=repair.file_path,
            repaired=True,
            status=repair.status,
            characters=len(
                repair.text
            ),
            chunks_rebuilt=chunks_rebuilt,
            embeddings_removed=(
                embeddings_removed
            ),
            error=repair.error,
        )

    except Exception as exc:
        return RepairOutcome(
            file_path=repair.file_path,
            repaired=False,
            status="failed",
            error=str(exc),
        )


def print_candidates(
    candidates: list[RepairCandidate],
) -> None:
    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        print()
        print(
            f"{index}. {candidate.file_path}"
        )

        print(
            f"   Integrity issues: "
            f"{candidate.issue_count}"
        )

        for message in candidate.issue_messages:
            print(
                f"   - {message}"
            )


def print_outcome(
    outcome: RepairOutcome,
) -> None:
    print()
    print("-" * 80)
    print(outcome.file_path)
    print(
        f"Repaired           : "
        f"{outcome.repaired}"
    )
    print(
        f"Status             : "
        f"{outcome.status}"
    )
    print(
        f"Characters         : "
        f"{outcome.characters}"
    )
    print(
        f"Chunks rebuilt     : "
        f"{outcome.chunks_rebuilt}"
    )
    print(
        f"Embeddings removed : "
        f"{outcome.embeddings_removed}"
    )

    if outcome.error:
        print(
            f"Error              : "
            f"{outcome.error}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Repair persisted PDF text that contains "
            "serialized extraction tuples."
        )
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
    )

    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
    )

    parser.add_argument(
        "--document-limit",
        type=int,
        default=100_000,
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Apply the repair. Without this flag, "
            "the command performs a dry run."
        ),
    )

    args = parser.parse_args()

    if not args.db.exists():
        print(
            f"Database not found: {args.db}"
        )
        return 1

    candidates = discover_candidates(
        database_path=args.db,
        document_limit=args.document_limit,
    )

    print()
    print("=" * 80)
    print("JARVIS SERIALIZED PDF TEXT REPAIR")
    print("=" * 80)
    print(f"Database   : {args.db}")
    print(
        f"Mode       : "
        f"{'APPLY' if args.apply else 'DRY RUN'}"
    )
    print(
        f"Candidates : {len(candidates)}"
    )

    print_candidates(
        candidates
    )

    if not candidates:
        print()
        print(
            "No serialized PDF text corruption "
            "was detected."
        )
        return 0

    if not args.apply:
        print()
        print("=" * 80)
        print(
            "Dry run complete. No database "
            "changes were made."
        )
        print(
            "Run again with --apply after "
            "reviewing the candidates."
        )
        print("=" * 80)
        return 0

    backup_path = create_database_backup(
        database_path=args.db,
        backup_directory=args.backup_dir,
    )

    print()
    print(
        f"Database backup created: "
        f"{backup_path}"
    )

    outcomes: list[RepairOutcome] = []

    for candidate in candidates:
        try:
            prepared = prepare_repair(
                candidate.file_path
            )

        except Exception as exc:
            outcome = RepairOutcome(
                file_path=candidate.file_path,
                repaired=False,
                status="preparation_failed",
                error=str(exc),
            )

            outcomes.append(outcome)
            print_outcome(outcome)
            continue

        outcome = apply_repair(
            database_path=args.db,
            repair=prepared,
        )

        outcomes.append(outcome)
        print_outcome(outcome)

    repaired = sum(
        1
        for outcome in outcomes
        if outcome.repaired
    )

    failed = len(outcomes) - repaired

    print()
    print("=" * 80)
    print("REPAIR SUMMARY")
    print("=" * 80)
    print(f"Candidates : {len(candidates)}")
    print(f"Repaired   : {repaired}")
    print(f"Failed     : {failed}")
    print(f"Backup     : {backup_path}")
    print("=" * 80)

    if failed:
        print()
        print(
            "One or more repairs failed. "
            "The successful repairs were committed "
            "per document."
        )

        print(
            "The original database backup is "
            f"available at: {backup_path}"
        )

        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
