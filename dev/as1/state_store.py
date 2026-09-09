from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SCHEMA_VERSION = 1
FINGERPRINT_VERSION = "as1-fingerprint-v1"

DEFAULT_STATE_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/as1_identity.sqlite"
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def open_state(
    path: Path = DEFAULT_STATE_DB,
) -> sqlite3.Connection:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )
    conn.execute(
        "PRAGMA foreign_keys=ON"
    )
    conn.execute(
        "PRAGMA synchronous=NORMAL"
    )
    conn.execute(
        "PRAGMA busy_timeout=5000"
    )

    return conn


def initialize_schema(
    conn: sqlite3.Connection,
) -> None:

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS as1_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS as1_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_type TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            objects_examined INTEGER NOT NULL DEFAULT 0,
            objects_changed INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS as1_identity_fingerprints (
            fingerprint_id INTEGER PRIMARY KEY AUTOINCREMENT,

            file_path TEXT NOT NULL,
            source_kind TEXT NOT NULL,

            runtime_document_id INTEGER,
            legacy_document_id INTEGER,

            sha256 TEXT,
            normalized_content_sha256 TEXT,

            -- Stored as hexadecimal text rather than SQLite
            -- INTEGER because unsigned SimHash values may
            -- exceed signed 64-bit SQLite integer range.
            simhash64_hex TEXT,

            normalized_chars INTEGER,
            normalized_title TEXT NOT NULL,

            size_bytes INTEGER NOT NULL,
            mtime_ns INTEGER,

            fingerprint_version TEXT NOT NULL,

            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            UNIQUE(file_path, fingerprint_version)
        );

        CREATE TABLE IF NOT EXISTS as1_object_state (
            file_path TEXT PRIMARY KEY,

            lifecycle TEXT NOT NULL,
            object_role TEXT,
            handler TEXT,

            identity_verdict TEXT,
            identity_layer TEXT,
            identity_confidence REAL,

            matched_path TEXT,

            review_required INTEGER NOT NULL DEFAULT 0,
            review_reason TEXT,

            last_seen_at TEXT NOT NULL,
            last_fingerprinted_at TEXT,

            state_version INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS as1_identity_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,

            file_path TEXT NOT NULL,
            event_type TEXT NOT NULL,

            previous_value TEXT,
            new_value TEXT,

            run_id INTEGER,

            created_at TEXT NOT NULL,

            FOREIGN KEY(run_id)
                REFERENCES as1_runs(run_id)
        );

        CREATE INDEX IF NOT EXISTS
            idx_as1_fp_sha256
        ON as1_identity_fingerprints(sha256);

        CREATE INDEX IF NOT EXISTS
            idx_as1_fp_normalized_sha
        ON as1_identity_fingerprints(
            normalized_content_sha256
        );

        CREATE INDEX IF NOT EXISTS
            idx_as1_fp_simhash
        ON as1_identity_fingerprints(
            simhash64_hex
        );

        CREATE INDEX IF NOT EXISTS
            idx_as1_fp_title
        ON as1_identity_fingerprints(
            normalized_title
        );

        CREATE INDEX IF NOT EXISTS
            idx_as1_fp_runtime_document
        ON as1_identity_fingerprints(
            runtime_document_id
        );

        CREATE INDEX IF NOT EXISTS
            idx_as1_state_lifecycle
        ON as1_object_state(lifecycle);

        CREATE INDEX IF NOT EXISTS
            idx_as1_state_review
        ON as1_object_state(review_required);
        """
    )

    metadata = {
        "schema_version":
            str(SCHEMA_VERSION),

        "fingerprint_version":
            FINGERPRINT_VERSION,

        "component":
            "Genesis AS1",

        "purpose":
            "Durable corpus identity and lifecycle state",
    }

    for key, value in metadata.items():
        conn.execute(
            """
            INSERT INTO as1_metadata(key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (key, value),
        )

    conn.commit()


def start_run(
    conn: sqlite3.Connection,
    run_type: str,
    notes: str | None = None,
) -> int:

    cursor = conn.execute(
        """
        INSERT INTO as1_runs(
            run_type,
            started_at,
            status,
            notes
        )
        VALUES (?, ?, 'running', ?)
        """,
        (
            run_type,
            utc_now(),
            notes,
        ),
    )

    conn.commit()

    return int(cursor.lastrowid)


def complete_run(
    conn: sqlite3.Connection,
    run_id: int,
    *,
    status: str,
    objects_examined: int,
    objects_changed: int,
    notes: str | None = None,
) -> None:

    conn.execute(
        """
        UPDATE as1_runs
        SET
            completed_at=?,
            status=?,
            objects_examined=?,
            objects_changed=?,
            notes=COALESCE(?, notes)
        WHERE run_id=?
        """,
        (
            utc_now(),
            status,
            objects_examined,
            objects_changed,
            notes,
            run_id,
        ),
    )

    conn.commit()


def simhash_to_hex(
    value: int | None,
) -> str | None:

    if value is None:
        return None

    return f"{value:016x}"


@dataclass(frozen=True)
class StoredFingerprint:
    file_path: str
    source_kind: str
    runtime_document_id: int | None
    legacy_document_id: int | None
    sha256: str | None
    normalized_content_sha256: str | None
    simhash64_hex: str | None
    normalized_chars: int | None
    normalized_title: str
    size_bytes: int
    mtime_ns: int | None
    fingerprint_version: str


def upsert_fingerprint(
    conn: sqlite3.Connection,
    fingerprint: StoredFingerprint,
) -> bool:
    """
    Returns True if state changed, False if the persisted
    fingerprint was already identical.
    """

    existing = conn.execute(
        """
        SELECT *
        FROM as1_identity_fingerprints
        WHERE file_path=?
          AND fingerprint_version=?
        LIMIT 1
        """,
        (
            fingerprint.file_path,
            fingerprint.fingerprint_version,
        ),
    ).fetchone()

    values = (
        fingerprint.source_kind,
        fingerprint.runtime_document_id,
        fingerprint.legacy_document_id,
        fingerprint.sha256,
        fingerprint.normalized_content_sha256,
        fingerprint.simhash64_hex,
        fingerprint.normalized_chars,
        fingerprint.normalized_title,
        fingerprint.size_bytes,
        fingerprint.mtime_ns,
    )

    changed = True

    if existing is not None:
        previous = (
            existing["source_kind"],
            existing["runtime_document_id"],
            existing["legacy_document_id"],
            existing["sha256"],
            existing["normalized_content_sha256"],
            existing["simhash64_hex"],
            existing["normalized_chars"],
            existing["normalized_title"],
            existing["size_bytes"],
            existing["mtime_ns"],
        )

        changed = previous != values

    now = utc_now()

    conn.execute(
        """
        INSERT INTO as1_identity_fingerprints(
            file_path,
            source_kind,
            runtime_document_id,
            legacy_document_id,
            sha256,
            normalized_content_sha256,
            simhash64_hex,
            normalized_chars,
            normalized_title,
            size_bytes,
            mtime_ns,
            fingerprint_version,
            created_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(file_path, fingerprint_version)
        DO UPDATE SET
            source_kind=excluded.source_kind,
            runtime_document_id=excluded.runtime_document_id,
            legacy_document_id=excluded.legacy_document_id,
            sha256=excluded.sha256,
            normalized_content_sha256=
                excluded.normalized_content_sha256,
            simhash64_hex=excluded.simhash64_hex,
            normalized_chars=excluded.normalized_chars,
            normalized_title=excluded.normalized_title,
            size_bytes=excluded.size_bytes,
            mtime_ns=excluded.mtime_ns,
            updated_at=excluded.updated_at
        """,
        (
            fingerprint.file_path,
            *values,
            fingerprint.fingerprint_version,
            now,
            now,
        ),
    )

    conn.commit()

    return changed


def upsert_object_state(
    conn: sqlite3.Connection,
    *,
    file_path: str,
    lifecycle: str,
    object_role: str | None,
    handler: str | None,
    identity_verdict: str | None,
    identity_layer: str | None,
    identity_confidence: float | None,
    matched_path: str | None,
    review_required: bool,
    review_reason: str | None,
    fingerprinted: bool,
) -> None:

    now = utc_now()

    conn.execute(
        """
        INSERT INTO as1_object_state(
            file_path,
            lifecycle,
            object_role,
            handler,
            identity_verdict,
            identity_layer,
            identity_confidence,
            matched_path,
            review_required,
            review_reason,
            last_seen_at,
            last_fingerprinted_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(file_path)
        DO UPDATE SET
            lifecycle=excluded.lifecycle,
            object_role=excluded.object_role,
            handler=excluded.handler,
            identity_verdict=excluded.identity_verdict,
            identity_layer=excluded.identity_layer,
            identity_confidence=
                excluded.identity_confidence,
            matched_path=excluded.matched_path,
            review_required=excluded.review_required,
            review_reason=excluded.review_reason,
            last_seen_at=excluded.last_seen_at,
            last_fingerprinted_at=
                CASE
                    WHEN excluded.last_fingerprinted_at
                         IS NOT NULL
                    THEN excluded.last_fingerprinted_at
                    ELSE as1_object_state.last_fingerprinted_at
                END
        """,
        (
            file_path,
            lifecycle,
            object_role,
            handler,
            identity_verdict,
            identity_layer,
            identity_confidence,
            matched_path,
            1 if review_required else 0,
            review_reason,
            now,
            now if fingerprinted else None,
        ),
    )

    conn.commit()


def record_event(
    conn: sqlite3.Connection,
    *,
    file_path: str,
    event_type: str,
    previous_value: str | None,
    new_value: str | None,
    run_id: int | None,
) -> None:

    conn.execute(
        """
        INSERT INTO as1_identity_events(
            file_path,
            event_type,
            previous_value,
            new_value,
            run_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            file_path,
            event_type,
            previous_value,
            new_value,
            run_id,
            utc_now(),
        ),
    )

    conn.commit()
