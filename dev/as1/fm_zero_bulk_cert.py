from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import time

from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from dev.as1.identity import (
    IdentityVerdict,
    build_fingerprint,
)

from dev.as1.object_router import (
    route_object,
)

from dev.as1.targeted_identity import (
    TargetedRuntimeIdentityResolver,
)


KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

LEGACY_DB = Path(
    "/media/abdullah/JARVISDATA/Knowledge/.jarvis/catalog.sqlite"
)

CANARY = (
    KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)

MAX_SOURCE_TEXT_CHARS = 2_000_000


def say(*args):
    print(*args, flush=True)


def ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row

    # Defensive query behavior.
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=5000")

    return conn


def table_exists(
    conn: sqlite3.Connection,
    table: str,
) -> bool:
    return (
        conn.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type IN ('table','view')
              AND name=?
            LIMIT 1
            """,
            (table,),
        ).fetchone()
        is not None
    )


def columns(
    conn: sqlite3.Connection,
    table: str,
) -> list[str]:
    if not table_exists(conn, table):
        return []

    return [
        str(row["name"])
        for row in conn.execute(
            f'PRAGMA table_info("{table}")'
        )
    ]


def first_existing(
    preferred: Iterable[str],
    available: Iterable[str],
) -> str | None:
    available_set = set(available)

    for name in preferred:
        if name in available_set:
            return name

    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def exact_row_by_path(
    conn: sqlite3.Connection,
    table: str,
    path: Path,
) -> dict | None:
    """
    Target ONE object only.

    No table is loaded into Python.
    """

    if not table_exists(conn, table):
        return None

    available = columns(conn, table)

    path_col = first_existing(
        (
            "file_path",
            "path",
            "document_path",
            "absolute_path",
            "source_path",
            "local_path",
            "relative_path",
        ),
        available,
    )

    if path_col is None:
        return None

    absolute = str(path)

    try:
        relative = str(
            path.relative_to(KNOWLEDGE_ROOT)
        )
    except ValueError:
        relative = absolute

    row = conn.execute(
        f'''
        SELECT *
        FROM "{table}"
        WHERE "{path_col}" = ?
           OR "{path_col}" = ?
        LIMIT 1
        ''',
        (
            absolute,
            relative,
        ),
    ).fetchone()

    if row is None:
        return None

    return dict(row)


def targeted_lifecycle(
    *,
    runtime: sqlite3.Connection,
    legacy: sqlite3.Connection,
    path: Path,
) -> dict:
    """
    Single-object equivalent of Pack 1B lifecycle resolution.

    Absolutely no whole-corpus Python indexes.
    """

    route = route_object(path)

    runtime_row = exact_row_by_path(
        runtime,
        "runtime_documents",
        path,
    )

    if runtime_row is not None:
        return {
            "lifecycle": "UNCHANGED_RUNTIME",
            "role": route.role.value,
            "handler": route.handler,
            "text_admissible":
                route.admissible_to_text_pipeline,
            "reason":
                "Exact file path already exists in runtime_documents.",
            "runtime": runtime_row,
            "classification": None,
            "discovered": None,
            "catalog": None,
            "legacy": None,
        }

    classification = exact_row_by_path(
        runtime,
        "knowledge_classifications",
        path,
    )

    if classification is not None:
        action = str(
            classification.get("action") or ""
        ).casefold()

        if action == "candidate":
            lifecycle = "ADMIT_CLASSIFIED"
        elif action == "ignore":
            lifecycle = "IGNORE"
        else:
            lifecycle = "REVIEW"

        return {
            "lifecycle": lifecycle,
            "role": route.role.value,
            "handler": route.handler,
            "text_admissible":
                route.admissible_to_text_pipeline,
            "reason":
                "Exact canonical classification record exists.",
            "runtime": None,
            "classification": classification,
            "discovered": None,
            "catalog": None,
            "legacy": None,
        }

    discovered = exact_row_by_path(
        runtime,
        "discovered_files",
        path,
    )

    if discovered is not None:
        return {
            "lifecycle": "CLASSIFY",
            "role": route.role.value,
            "handler": route.handler,
            "text_admissible":
                route.admissible_to_text_pipeline,
            "reason":
                "Exact discovered_files record exists but classification is absent.",
            "runtime": None,
            "classification": None,
            "discovered": discovered,
            "catalog": None,
            "legacy": None,
        }

    catalog = exact_row_by_path(
        runtime,
        "catalog_documents",
        path,
    )

    legacy_row = exact_row_by_path(
        legacy,
        "documents",
        path,
    )

    if (
        catalog is not None
        or legacy_row is not None
    ):
        return {
            "lifecycle":
                "BRIDGE_TO_CANONICAL_DISCOVERY",
            "role": route.role.value,
            "handler": route.handler,
            "text_admissible":
                route.admissible_to_text_pipeline,
            "reason":
                "Object exists in legacy/catalog state but not canonical discovery/runtime.",
            "runtime": None,
            "classification": None,
            "discovered": None,
            "catalog": catalog,
            "legacy": legacy_row,
        }

    return {
        "lifecycle": "DISCOVER",
        "role": route.role.value,
        "handler": route.handler,
        "text_admissible":
            route.admissible_to_text_pipeline,
        "reason":
            "Physical object is unknown to targeted canonical and legacy lookups.",
        "runtime": None,
        "classification": None,
        "discovered": None,
        "catalog": None,
        "legacy": None,
    }


def record_digest(
    lifecycle: dict,
) -> str | None:
    """
    Prefer an already-stored SHA.

    Hash the physical PDF only if needed.
    """

    for section in (
        "runtime",
        "catalog",
        "legacy",
        "discovered",
    ):
        record = lifecycle.get(section)

        if not record:
            continue

        for key in (
            "sha256",
            "fingerprint",
            "content_sha256",
        ):
            value = record.get(key)

            if value:
                text = str(value).strip()

                if len(text) == 64:
                    return text

    return None


def document_identity(
    conn: sqlite3.Connection,
    path: Path,
) -> tuple[int | None, dict | None]:
    """
    Resolve only this FM's legacy document ID.
    """

    row = exact_row_by_path(
        conn,
        "documents",
        path,
    )

    if row is None:
        return None, None

    for key in (
        "id",
        "document_id",
        "doc_id",
    ):
        value = row.get(key)

        if value is not None:
            try:
                return int(value), row
            except (TypeError, ValueError):
                continue

    return None, row


def fetch_text_rows(
    conn: sqlite3.Connection,
    *,
    table: str,
    document_id: int,
    maximum_chars: int,
) -> str | None:
    """
    Fetch text for ONE legacy document ID only.

    No unrestricted SELECT.
    """

    if not table_exists(conn, table):
        return None

    available = columns(
        conn,
        table,
    )

    id_col = first_existing(
        (
            "document_id",
            "doc_id",
        ),
        available,
    )

    text_col = first_existing(
        (
            "content_text",
            "extracted_text",
            "document_text",
            "text",
            "content",
            "body",
            "page_text",
        ),
        available,
    )

    if (
        id_col is None
        or text_col is None
    ):
        return None

    order_col = first_existing(
        (
            "page_number",
            "page_index",
            "page",
            "sequence",
            "chunk_index",
            "id",
        ),
        available,
    )

    order_sql = (
        f' ORDER BY "{order_col}"'
        if order_col
        else ""
    )

    cursor = conn.execute(
        f'''
        SELECT "{text_col}"
        FROM "{table}"
        WHERE "{id_col}" = ?
        {order_sql}
        ''',
        (document_id,),
    )

    parts: list[str] = []
    chars = 0

    for row in cursor:
        value = row[0]

        if value is None:
            continue

        text = str(value)

        remaining = (
            maximum_chars - chars
        )

        if remaining <= 0:
            break

        if len(text) > remaining:
            text = text[:remaining]

        parts.append(text)
        chars += len(text)

        if chars >= maximum_chars:
            break

    if not parts:
        return None

    result = "\n".join(parts)

    return (
        result
        if result.strip()
        else None
    )


def targeted_legacy_text(
    conn: sqlite3.Connection,
    path: Path,
) -> tuple[str | None, str | None]:
    """
    Try only text tables associated with this one legacy
    document.

    Does not enumerate corpus records.
    """

    document_id, _ = document_identity(
        conn,
        path,
    )

    if document_id is None:
        return None, None

    for table in (
        "document_text",
        "document_pages",
    ):
        text = fetch_text_rows(
            conn,
            table=table,
            document_id=document_id,
            maximum_chars=MAX_SOURCE_TEXT_CHARS,
        )

        if text:
            return text, table

    return None, None


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=RUNTIME_DB,
    )

    parser.add_argument(
        "--legacy-db",
        type=Path,
        default=LEGACY_DB,
    )

    parser.add_argument(
        "--max-candidates",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--max-runtime-content-chars",
        type=int,
        default=4_000_000,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    started = time.monotonic()

    say()
    say("=== STEP 1 — PHYSICAL CANARY ===")
    say("path:", CANARY)

    if not CANARY.is_file():
        say("physical: FAIL")
        return 2

    stat = CANARY.stat()

    say("physical: PASS")
    say("size    :", f"{stat.st_size:,} bytes")

    say()
    say("=== STEP 2 — OPEN DATABASES READ ONLY ===")

    runtime = ro(args.runtime_db)
    legacy = ro(args.legacy_db)

    say("runtime DB: OPEN")
    say("legacy DB : OPEN")

    try:
        say()
        say("=== STEP 3 — TARGETED LIFECYCLE ===")

        lifecycle = targeted_lifecycle(
            runtime=runtime,
            legacy=legacy,
            path=CANARY,
        )

        say(
            "lifecycle      :",
            lifecycle["lifecycle"],
        )
        say(
            "role           :",
            lifecycle["role"],
        )
        say(
            "handler        :",
            lifecycle["handler"],
        )
        say(
            "text admissible:",
            lifecycle["text_admissible"],
        )
        say(
            "reason         :",
            lifecycle["reason"],
        )

        if lifecycle["role"] != "DOCUMENT":
            say("CERTIFICATION: FAIL")
            say(
                "FM did not route as DOCUMENT."
            )
            return 3

        say()
        say("=== STEP 4 — SINGLE-OBJECT SHA ===")

        digest = record_digest(
            lifecycle
        )

        if digest:
            say(
                "SHA source: existing catalog metadata"
            )
        else:
            say(
                "SHA source: physical FM file"
            )

            digest = sha256_file(
                CANARY
            )

        say("sha256:", digest)

        say()
        say("=== STEP 5 — TARGETED LEGACY TEXT ===")

        candidate_text, text_source = (
            targeted_legacy_text(
                legacy,
                CANARY,
            )
        )

        if candidate_text:
            say("text       : AVAILABLE")
            say(
                "text source:",
                text_source,
            )
            say(
                "text chars :",
                f"{len(candidate_text):,}",
            )
        else:
            say("text       : UNAVAILABLE")
            say("text source: -")

        say()
        say("=== STEP 6 — BUILD FM FINGERPRINT ===")

        fingerprint = build_fingerprint(
            path=CANARY,
            sha256=digest,
            text=candidate_text,
        )

        say(
            "normalized title:",
            fingerprint.normalized_title,
        )

        say(
            "normalized chars:",
            (
                f"{fingerprint.normalized_chars:,}"
                if fingerprint.normalized_chars
                is not None
                else "-"
            ),
        )

        say(
            "normalized SHA  :",
            fingerprint.normalized_content_sha256
            or "-",
        )

        say(
            "simhash64       :",
            fingerprint.simhash64
            if fingerprint.simhash64
            is not None
            else "-",
        )

        say()
        say("=== STEP 7 — TARGETED RUNTIME IDENTITY ===")

        resolver = (
            TargetedRuntimeIdentityResolver(
                runtime,
                maximum_candidates=(
                    args.max_candidates
                ),
                maximum_content_chars=(
                    args.max_runtime_content_chars
                ),
            )
        )

        say(
            "resolver initialized; "
            "no runtime corpus index constructed"
        )

        result = resolver.resolve(
            fingerprint=fingerprint,
            candidate_text=candidate_text,
        )

        say()
        say("=== STEP 8 — VERDICT ===")

        say(
            "verdict      :",
            result.verdict.value,
        )
        say(
            "layer        :",
            result.layer,
        )
        say(
            "confidence   :",
            f"{result.confidence:.3f}",
        )
        say(
            "matched path :",
            result.matched_path or "-",
        )
        say(
            "reason       :",
            result.reason,
        )

        say(
            "content rows loaded :",
            resolver.content_rows_loaded,
        )

        say(
            "content rows skipped:",
            resolver.content_rows_skipped,
        )

        say()
        say("=== STEP 9 — CERTIFICATION ===")

        if result.verdict in {
            IdentityVerdict.EXACT_DUPLICATE,
            IdentityVerdict.CONTENT_DUPLICATE,
            IdentityVerdict.NEAR_DUPLICATE,
            IdentityVerdict.STRUCTURAL_MATCH,
        }:
            if result.matched_path:
                status = "PASS"
                cert_reason = (
                    "Bounded targeted SQL proved an identity "
                    "relationship and returned the runtime path."
                )
            else:
                status = "FAIL"
                cert_reason = (
                    "Identity relationship lacked a runtime path."
                )

        elif result.verdict == IdentityVerdict.UNRESOLVED:
            status = "PASS_WITH_REVIEW"
            cert_reason = (
                "No bounded identity collision was proven; "
                "resolver correctly avoided claiming DISTINCT."
            )

        elif result.verdict == IdentityVerdict.DISTINCT:
            status = "FAIL"
            cert_reason = (
                "Bounded targeted lookup is not allowed to "
                "claim global DISTINCT."
            )

        else:
            status = "FAIL"
            cert_reason = (
                "Unexpected identity verdict."
            )

        elapsed = (
            time.monotonic()
            - started
        )

        say("status:", status)
        say("reason:", cert_reason)

        say()
        say("=== STEP 10 — SAFETY ===")
        say("physical objects processed : 1")
        say("recursive corpus scan       : 0")
        say("bulk runtime loader calls   : 0")
        say("bulk legacy loader calls    : 0")
        say("runtime Python index        : 0")
        say("database writes             : 0")
        say("source mutations            : 0")
        say("runtime mutations           : 0")
        say(
            "elapsed                     :",
            f"{elapsed:.2f}s",
        )

        payload = {
            "schema":
                "genesis-as1-pack2-r2-r3-v1",

            "read_only":
                True,

            "canary":
                str(CANARY),

            "lifecycle":
                lifecycle["lifecycle"],

            "role":
                lifecycle["role"],

            "handler":
                lifecycle["handler"],

            "fingerprint":
                asdict(fingerprint),

            "identity":
                asdict(result),

            "candidate_text_source":
                text_source,

            "runtime_content_rows_loaded":
                resolver.content_rows_loaded,

            "runtime_content_rows_skipped":
                resolver.content_rows_skipped,

            "certification_status":
                status,

            "certification_reason":
                cert_reason,

            "elapsed_seconds":
                elapsed,
        }

        if args.json:
            args.json.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            args.json.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                encoding="utf-8",
            )

            say(
                "JSON report                :",
                args.json,
            )

        say()
        say("============================================================")

        if status == "PASS":
            say(
                " GENESIS AS1 PACK 2-R2-R3 CERTIFIED"
            )

        elif status == "PASS_WITH_REVIEW":
            say(
                " GENESIS AS1 PACK 2-R2-R3 "
                "CERTIFIED WITH REVIEW"
            )

        else:
            say(
                " GENESIS AS1 PACK 2-R2-R3 FAILED"
            )

        say(
            " ZERO BULK LOADERS — ZERO DATABASE WRITES"
        )
        say("============================================================")

        return (
            0
            if status in {
                "PASS",
                "PASS_WITH_REVIEW",
            }
            else 1
        )

    finally:
        runtime.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
