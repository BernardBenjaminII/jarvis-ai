from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path

from dev.as1.identity import (
    build_fingerprint,
)

from dev.as1.object_router import (
    route_object,
)

from dev.as1.state_store import (
    DEFAULT_STATE_DB,
    FINGERPRINT_VERSION,
    StoredFingerprint,
    complete_run,
    initialize_schema,
    open_state,
    record_event,
    simhash_to_hex,
    start_run,
    upsert_fingerprint,
    upsert_object_state,
)


KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)

LEGACY_DB = Path(
    "/media/abdullah/JARVISDATA/Knowledge/"
    ".jarvis/catalog.sqlite"
)

CANARY = (
    KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


def ro(path: Path):
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def table_columns(conn, table):
    return {
        str(row["name"])
        for row in conn.execute(
            f'PRAGMA table_info("{table}")'
        )
    }


def targeted_row(conn, table, path):

    exists = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        LIMIT 1
        """,
        (table,),
    ).fetchone()

    if exists is None:
        return None

    cols = table_columns(
        conn,
        table,
    )

    path_col = next(
        (
            c for c in (
                "file_path",
                "path",
                "document_path",
            )
            if c in cols
        ),
        None,
    )

    if path_col is None:
        return None

    try:
        relative = str(
            path.relative_to(
                KNOWLEDGE_ROOT
            )
        )
    except ValueError:
        relative = str(path)

    row = conn.execute(
        f'''
        SELECT *
        FROM "{table}"
        WHERE "{path_col}"=?
           OR "{path_col}"=?
        LIMIT 1
        ''',
        (
            str(path),
            relative,
        ),
    ).fetchone()

    return (
        dict(row)
        if row is not None
        else None
    )


def targeted_text(
    legacy,
    path: Path,
    max_chars: int = 2_000_000,
):

    doc = targeted_row(
        legacy,
        "documents",
        path,
    )

    if not doc:
        return None, None

    document_id = doc.get("id")

    if document_id is None:
        return None, doc

    for table in (
        "document_text",
        "document_pages",
    ):

        exists = legacy.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type='table'
              AND name=?
            """,
            (table,),
        ).fetchone()

        if exists is None:
            continue

        cols = table_columns(
            legacy,
            table,
        )

        id_col = next(
            (
                c for c in (
                    "document_id",
                    "doc_id",
                )
                if c in cols
            ),
            None,
        )

        text_col = next(
            (
                c for c in (
                    "content_text",
                    "extracted_text",
                    "text",
                    "content",
                    "page_text",
                )
                if c in cols
            ),
            None,
        )

        if (
            id_col is None
            or text_col is None
        ):
            continue

        parts = []
        chars = 0

        cursor = legacy.execute(
            f'''
            SELECT "{text_col}"
            FROM "{table}"
            WHERE "{id_col}"=?
            ''',
            (document_id,),
        )

        for row in cursor:
            if row[0] is None:
                continue

            value = str(row[0])

            remaining = (
                max_chars - chars
            )

            if remaining <= 0:
                break

            value = value[:remaining]

            parts.append(value)
            chars += len(value)

        if parts:
            return "\n".join(parts), doc

    return None, doc


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--state-db",
        type=Path,
        default=DEFAULT_STATE_DB,
    )

    args = parser.parse_args()

    print(
        "FM canary:",
        CANARY,
        flush=True,
    )

    if not CANARY.is_file():
        print(
            "FAIL: FM canary missing",
            flush=True,
        )
        return 2

    runtime = ro(RUNTIME_DB)
    legacy = ro(LEGACY_DB)

    state = open_state(
        args.state_db
    )

    try:
        initialize_schema(state)

        run_id = start_run(
            state,
            "pack3_canary_seed",
            "FM 3-06.11 durable fingerprint seed",
        )

        route = route_object(
            CANARY
        )

        runtime_row = targeted_row(
            runtime,
            "runtime_documents",
            CANARY,
        )

        classification = targeted_row(
            runtime,
            "knowledge_classifications",
            CANARY,
        )

        discovered = targeted_row(
            runtime,
            "discovered_files",
            CANARY,
        )

        catalog = targeted_row(
            runtime,
            "catalog_documents",
            CANARY,
        )

        legacy_text, legacy_doc = (
            targeted_text(
                legacy,
                CANARY,
            )
        )

        if runtime_row:
            lifecycle = "UNCHANGED_RUNTIME"

        elif classification:
            action = str(
                classification.get(
                    "action"
                )
                or ""
            ).casefold()

            lifecycle = (
                "ADMIT_CLASSIFIED"
                if action == "candidate"
                else "REVIEW"
            )

        elif discovered:
            lifecycle = "CLASSIFY"

        elif (
            catalog
            or legacy_doc
        ):
            lifecycle = (
                "BRIDGE_TO_CANONICAL_DISCOVERY"
            )

        else:
            lifecycle = "DISCOVER"

        digest = None

        for record in (
            runtime_row,
            catalog,
            legacy_doc,
            discovered,
        ):
            if not record:
                continue

            value = record.get(
                "sha256"
            )

            if value:
                digest = str(value)
                break

        if not digest:
            digest = sha256_file(
                CANARY
            )

        fingerprint = build_fingerprint(
            path=CANARY,
            sha256=digest,
            text=legacy_text,
        )

        stat = CANARY.stat()

        runtime_id = (
            int(runtime_row["id"])
            if runtime_row
            and runtime_row.get("id")
            is not None
            else None
        )

        legacy_id = (
            int(legacy_doc["id"])
            if legacy_doc
            and legacy_doc.get("id")
            is not None
            else None
        )

        stored = StoredFingerprint(
            file_path=str(CANARY),
            source_kind=(
                "runtime"
                if runtime_row
                else "legacy_bridge"
            ),
            runtime_document_id=
                runtime_id,
            legacy_document_id=
                legacy_id,
            sha256=
                fingerprint.sha256,
            normalized_content_sha256=
                fingerprint
                .normalized_content_sha256,
            simhash64_hex=
                simhash_to_hex(
                    fingerprint.simhash64
                ),
            normalized_chars=
                fingerprint.normalized_chars,
            normalized_title=
                fingerprint.normalized_title,
            size_bytes=
                stat.st_size,
            mtime_ns=
                stat.st_mtime_ns,
            fingerprint_version=
                FINGERPRINT_VERSION,
        )

        changed = upsert_fingerprint(
            state,
            stored,
        )

        # Pack 2-R2-R3 established this canary as
        # PASS_WITH_REVIEW / UNRESOLVED.
        upsert_object_state(
            state,
            file_path=str(CANARY),
            lifecycle=lifecycle,
            object_role=
                route.role.value,
            handler=
                route.handler,
            identity_verdict=
                "UNRESOLVED",
            identity_layer=
                "bounded_sql",
            identity_confidence=
                0.50,
            matched_path=
                None,
            review_required=
                True,
            review_reason=(
                "Global identity remains unresolved until "
                "the durable fingerprint index is populated."
            ),
            fingerprinted=True,
        )

        if changed:
            record_event(
                state,
                file_path=str(CANARY),
                event_type=
                    "fingerprint_upsert",
                previous_value=None,
                new_value=
                    FINGERPRINT_VERSION,
                run_id=run_id,
            )

        complete_run(
            state,
            run_id,
            status="pass",
            objects_examined=1,
            objects_changed=(
                1 if changed else 0
            ),
        )

        print()
        print(
            "=== PACK 3 CANARY STATE ==="
        )

        print(
            "lifecycle             :",
            lifecycle,
        )

        print(
            "role                  :",
            route.role.value,
        )

        print(
            "sha256                :",
            fingerprint.sha256,
        )

        print(
            "normalized SHA        :",
            fingerprint
            .normalized_content_sha256
            or "-",
        )

        print(
            "normalized chars      :",
            fingerprint
            .normalized_chars
            or 0,
        )

        print(
            "simhash64             :",
            simhash_to_hex(
                fingerprint.simhash64
            )
            or "-",
        )

        print(
            "fingerprint changed   :",
            changed,
        )

        print(
            "state DB              :",
            args.state_db,
        )

        print()
        print(
            "PACK 3 CANARY SEED: PASS"
        )

        return 0

    finally:
        runtime.close()
        legacy.close()
        state.close()


if __name__ == "__main__":
    raise SystemExit(main())
