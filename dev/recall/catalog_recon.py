from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Iterable


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

DEFAULT_AS1_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/as1_identity.sqlite"
)

DEFAULT_LEGACY_DB = Path(
    "/media/abdullah/JARVISDATA/Knowledge/.jarvis/catalog.sqlite"
)

DEFAULT_KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

FM_CANARY = (
    DEFAULT_KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)


def ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def table_names(
    conn: sqlite3.Connection,
) -> list[str]:
    return [
        str(row["name"])
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type IN ('table','view')
            ORDER BY name
            """
        )
    ]


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
    names: Iterable[str],
    available: Iterable[str],
) -> str | None:
    available = set(available)

    for name in names:
        if name in available:
            return name

    return None


def safe_count(
    conn: sqlite3.Connection,
    table: str,
) -> int | None:
    if not table_exists(conn, table):
        return None

    try:
        row = conn.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()

        return int(row[0])

    except sqlite3.Error:
        return None


def matching_tables(
    conn: sqlite3.Connection,
    terms: Iterable[str],
) -> list[dict]:
    results = []

    for table in table_names(conn):
        cols = columns(conn, table)

        haystack = (
            table + " " + " ".join(cols)
        ).casefold()

        matched = [
            term
            for term in terms
            if term.casefold() in haystack
        ]

        if matched:
            results.append(
                {
                    "table": table,
                    "columns": cols,
                    "matched_terms": matched,
                }
            )

    return results


def exact_path_rows(
    conn: sqlite3.Connection,
    path: Path,
) -> list[dict]:
    """
    Search only tables with plausible path columns.

    Every query is exact-path targeted.
    """

    absolute = str(path)

    try:
        relative = str(
            path.relative_to(
                DEFAULT_KNOWLEDGE_ROOT
            )
        )
    except ValueError:
        relative = absolute

    results = []

    for table in table_names(conn):
        cols = columns(conn, table)

        path_col = first_existing(
            (
                "file_path",
                "path",
                "source_path",
                "document_path",
                "absolute_path",
                "relative_path",
                "local_path",
            ),
            cols,
        )

        if path_col is None:
            continue

        try:
            row = conn.execute(
                f'''
                SELECT *
                FROM "{table}"
                WHERE "{path_col}"=?
                   OR "{path_col}"=?
                LIMIT 1
                ''',
                (
                    absolute,
                    relative,
                ),
            ).fetchone()

        except sqlite3.Error:
            continue

        if row is not None:
            results.append(
                {
                    "table": table,
                    "path_column": path_col,
                    "row": dict(row),
                }
            )

    return results


def runtime_canary(
    runtime: sqlite3.Connection,
    path: Path,
) -> dict:
    result = {
        "runtime_document": None,
        "runtime_id": None,
        "chunk_hits": [],
        "fts_hits": [],
        "embedding_hits": [],
    }

    if not table_exists(
        runtime,
        "runtime_documents",
    ):
        return result

    row = runtime.execute(
        """
        SELECT
            id,
            file_path,
            sha256,
            title,
            media_type,
            content_chars
        FROM runtime_documents
        WHERE file_path=?
        LIMIT 1
        """,
        (str(path),),
    ).fetchone()

    if row is None:
        return result

    result["runtime_document"] = dict(row)
    runtime_id = int(row["id"])
    result["runtime_id"] = runtime_id

    for table in table_names(runtime):
        cols = columns(runtime, table)

        lower_name = table.casefold()

        # ----------------------------------------------------
        # Chunk-like tables
        # ----------------------------------------------------

        if (
            "chunk" in lower_name
            or "passage" in lower_name
            or "segment" in lower_name
        ):
            doc_col = first_existing(
                (
                    "runtime_document_id",
                    "document_id",
                    "doc_id",
                    "source_document_id",
                ),
                cols,
            )

            if doc_col:
                try:
                    count = runtime.execute(
                        f'''
                        SELECT COUNT(*)
                        FROM "{table}"
                        WHERE "{doc_col}"=?
                        ''',
                        (runtime_id,),
                    ).fetchone()[0]

                    if int(count) > 0:
                        result["chunk_hits"].append(
                            {
                                "table": table,
                                "document_column": doc_col,
                                "count": int(count),
                            }
                        )
                except sqlite3.Error:
                    pass

        # ----------------------------------------------------
        # Embedding/vector-like tables
        # ----------------------------------------------------

        if any(
            token in lower_name
            for token in (
                "embed",
                "vector",
                "semantic",
            )
        ):
            doc_col = first_existing(
                (
                    "runtime_document_id",
                    "document_id",
                    "doc_id",
                    "source_document_id",
                ),
                cols,
            )

            if doc_col:
                try:
                    count = runtime.execute(
                        f'''
                        SELECT COUNT(*)
                        FROM "{table}"
                        WHERE "{doc_col}"=?
                        ''',
                        (runtime_id,),
                    ).fetchone()[0]

                    if int(count) > 0:
                        result["embedding_hits"].append(
                            {
                                "table": table,
                                "document_column": doc_col,
                                "count": int(count),
                            }
                        )
                except sqlite3.Error:
                    pass

    # --------------------------------------------------------
    # FTS tables are often virtual and may not expose doc IDs
    # consistently. Record their presence/schema first.
    # --------------------------------------------------------

    fts_tables = runtime.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE sql LIKE '%VIRTUAL TABLE%'
          AND sql LIKE '%fts%'
        ORDER BY name
        """
    ).fetchall()

    for fts in fts_tables:
        result["fts_hits"].append(
            {
                "table": str(fts["name"]),
                "sql": str(fts["sql"] or ""),
                "columns": columns(
                    runtime,
                    str(fts["name"]),
                ),
            }
        )

    return result


def as1_canary(
    as1: sqlite3.Connection,
    path: Path,
) -> dict:
    result = {}

    if table_exists(
        as1,
        "as1_identity_fingerprints",
    ):
        row = as1.execute(
            """
            SELECT *
            FROM as1_identity_fingerprints
            WHERE file_path=?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (str(path),),
        ).fetchone()

        result["fingerprint"] = (
            dict(row)
            if row is not None
            else None
        )

    if table_exists(
        as1,
        "as1_object_state",
    ):
        row = as1.execute(
            """
            SELECT *
            FROM as1_object_state
            WHERE file_path=?
            LIMIT 1
            """,
            (str(path),),
        ).fetchone()

        result["object_state"] = (
            dict(row)
            if row is not None
            else None
        )

    return result


def summarize_tables(
    conn: sqlite3.Connection,
) -> list[dict]:
    """
    Identify tables relevant to catalog awareness/retrieval.

    No content blobs are selected.
    """

    keywords = (
        "catalog",
        "document",
        "discover",
        "classif",
        "chunk",
        "fts",
        "embed",
        "vector",
        "taxonomy",
        "subject",
        "topic",
        "author",
        "metadata",
        "source",
        "knowledge",
    )

    relevant = matching_tables(
        conn,
        keywords,
    )

    summaries = []

    for item in relevant:
        table = item["table"]

        summaries.append(
            {
                "table": table,
                "columns": item["columns"],
                "count": safe_count(
                    conn,
                    table,
                ),
                "matched_terms":
                    item["matched_terms"],
            }
        )

    return summaries


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--as1-db",
        type=Path,
        default=DEFAULT_AS1_DB,
    )

    parser.add_argument(
        "--legacy-db",
        type=Path,
        default=DEFAULT_LEGACY_DB,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    args = parser.parse_args()

    for path in (
        args.runtime_db,
        args.as1_db,
        args.legacy_db,
    ):
        if not path.is_file():
            print(
                "FAIL: missing DB:",
                path,
                flush=True,
            )
            return 2

    runtime = ro(args.runtime_db)
    as1 = ro(args.as1_db)
    legacy = ro(args.legacy_db)

    try:
        report = {
            "runtime": {},
            "as1": {},
            "legacy": {},
            "canary": {},
        }

        print()
        print(
            "=== 1. DATABASE INVENTORY ==="
        )

        for name, conn in (
            ("runtime", runtime),
            ("as1", as1),
            ("legacy", legacy),
        ):
            tables = table_names(conn)

            report[name]["tables"] = tables

            print(
                f"{name:8} tables :",
                len(tables),
            )

        print()
        print(
            "=== 2. RUNTIME KNOWLEDGE TABLES ==="
        )

        runtime_summary = summarize_tables(
            runtime
        )

        report["runtime"][
            "relevant_tables"
        ] = runtime_summary

        for item in runtime_summary:
            print()
            print(
                "TABLE:",
                item["table"],
            )
            print(
                "  rows    :",
                item["count"],
            )
            print(
                "  columns :",
                ", ".join(
                    item["columns"]
                ),
            )

        print()
        print(
            "=== 3. LEGACY/CATALOG KNOWLEDGE TABLES ==="
        )

        legacy_summary = summarize_tables(
            legacy
        )

        report["legacy"][
            "relevant_tables"
        ] = legacy_summary

        for item in legacy_summary:
            print()
            print(
                "TABLE:",
                item["table"],
            )
            print(
                "  rows    :",
                item["count"],
            )
            print(
                "  columns :",
                ", ".join(
                    item["columns"]
                ),
            )

        print()
        print(
            "=== 4. AS1 IDENTITY TABLES ==="
        )

        as1_summary = summarize_tables(
            as1
        )

        report["as1"][
            "relevant_tables"
        ] = as1_summary

        for item in as1_summary:
            print()
            print(
                "TABLE:",
                item["table"],
            )
            print(
                "  rows    :",
                item["count"],
            )
            print(
                "  columns :",
                ", ".join(
                    item["columns"]
                ),
            )

        print()
        print(
            "=== 5. RETRIEVAL SUBSYSTEM DISCOVERY ==="
        )

        retrieval_terms = (
            "chunk",
            "fts",
            "embed",
            "vector",
            "semantic",
            "bm25",
            "rank",
            "retriev",
        )

        retrieval_tables = matching_tables(
            runtime,
            retrieval_terms,
        )

        report["runtime"][
            "retrieval_tables"
        ] = retrieval_tables

        if not retrieval_tables:
            print(
                "No retrieval-oriented runtime tables detected."
            )

        for item in retrieval_tables:
            print()
            print(
                "RETRIEVAL TABLE:",
                item["table"],
            )
            print(
                "  matches :",
                ", ".join(
                    item["matched_terms"]
                ),
            )
            print(
                "  columns :",
                ", ".join(
                    item["columns"]
                ),
            )

        print()
        print(
            "=== 6. FTS VIRTUAL TABLES ==="
        )

        fts_rows = runtime.execute(
            """
            SELECT
                name,
                sql
            FROM sqlite_master
            WHERE sql LIKE '%VIRTUAL TABLE%'
              AND lower(sql) LIKE '%fts%'
            ORDER BY name
            """
        ).fetchall()

        report["runtime"]["fts_tables"] = [
            {
                "name": str(row["name"]),
                "sql": str(row["sql"] or ""),
            }
            for row in fts_rows
        ]

        if not fts_rows:
            print(
                "No SQLite FTS virtual tables detected."
            )

        for row in fts_rows:
            print(
                row["name"],
            )
            print(
                " ",
                row["sql"],
            )

        print()
        print(
            "=== 7. FM 3-06.11 END-TO-END CANARY ==="
        )

        print(
            "physical path:",
            FM_CANARY,
        )

        physical = FM_CANARY.is_file()

        print(
            "physical     :",
            "PASS"
            if physical
            else "FAIL",
        )

        legacy_rows = exact_path_rows(
            legacy,
            FM_CANARY,
        )

        runtime_rows = exact_path_rows(
            runtime,
            FM_CANARY,
        )

        as1_state = as1_canary(
            as1,
            FM_CANARY,
        )

        runtime_state = runtime_canary(
            runtime,
            FM_CANARY,
        )

        report["canary"] = {
            "path": str(FM_CANARY),
            "physical": physical,
            "legacy_rows":
                legacy_rows,
            "runtime_rows":
                runtime_rows,
            "as1":
                as1_state,
            "runtime_retrieval":
                runtime_state,
        }

        print()
        print(
            "Legacy/catalog exact-path hits:",
            len(legacy_rows),
        )

        for item in legacy_rows:
            print(
                "  ",
                item["table"],
            )

        print()
        print(
            "Runtime exact-path hits:",
            len(runtime_rows),
        )

        for item in runtime_rows:
            print(
                "  ",
                item["table"],
            )

        print()
        print(
            "AS1 fingerprint:",
            (
                "YES"
                if as1_state.get(
                    "fingerprint"
                )
                else "NO"
            ),
        )

        print(
            "AS1 object state:",
            (
                "YES"
                if as1_state.get(
                    "object_state"
                )
                else "NO"
            ),
        )

        runtime_doc = runtime_state.get(
            "runtime_document"
        )

        print(
            "runtime_documents:",
            (
                "YES"
                if runtime_doc
                else "NO"
            ),
        )

        if runtime_doc:
            print(
                "  runtime id   :",
                runtime_doc["id"],
            )
            print(
                "  title        :",
                runtime_doc["title"],
            )
            print(
                "  content chars:",
                runtime_doc["content_chars"],
            )

        print(
            "chunk mappings :",
            runtime_state[
                "chunk_hits"
            ],
        )

        print(
            "embedding maps :",
            runtime_state[
                "embedding_hits"
            ],
        )

        print(
            "FTS tables     :",
            [
                item["table"]
                for item
                in runtime_state[
                    "fts_hits"
                ]
            ],
        )

        print()
        print(
            "=== 8. CANARY DIAGNOSIS ==="
        )

        if not physical:
            diagnosis = (
                "SOURCE_MISSING"
            )

        elif not legacy_rows:
            diagnosis = (
                "CATALOG_AWARENESS_GAP"
            )

        elif not runtime_doc:
            diagnosis = (
                "ASSIMILATION_GAP"
            )

        elif (
            not runtime_state["chunk_hits"]
            and not runtime_state[
                "fts_hits"
            ]
            and not runtime_state[
                "embedding_hits"
            ]
        ):
            diagnosis = (
                "RETRIEVAL_INDEX_GAP"
            )

        else:
            diagnosis = (
                "CONTENT_PRESENT_TRACE_QUERY_PATH_NEXT"
            )

        report["canary"][
            "diagnosis"
        ] = diagnosis

        print(
            "diagnosis:",
            diagnosis,
        )

        print()
        print(
            "=== 9. RECONNAISSANCE SUMMARY ==="
        )

        print(
            "Catalog awareness source(s):"
        )

        candidates = []

        for item in (
            legacy_summary
            + runtime_summary
        ):
            name = (
                item["table"]
                .casefold()
            )

            if any(
                token in name
                for token in (
                    "catalog",
                    "document",
                    "classif",
                    "discover",
                    "taxonomy",
                    "metadata",
                )
            ):
                candidates.append(
                    item["table"]
                )

        for candidate in sorted(
            set(candidates)
        ):
            print(
                "  -",
                candidate,
            )

        print()
        print(
            "Retrieval storage candidates:"
        )

        for item in retrieval_tables:
            print(
                "  -",
                item["table"],
            )

        if args.json:
            args.json.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            args.json.write_text(
                json.dumps(
                    report,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                encoding="utf-8",
            )

            print()
            print(
                "JSON report:",
                args.json,
            )

        print()
        print(
            "GENESIS RECALL R1 DATABASE RECON: PASS"
        )

        return 0

    finally:
        runtime.close()
        as1.close()
        legacy.close()


if __name__ == "__main__":
    raise SystemExit(main())
