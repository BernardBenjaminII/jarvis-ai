from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time

from pathlib import Path
from typing import Any


DEFAULT_RUNTIME_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/"
    "knowledge/catalog.sqlite"
)

KNOWLEDGE_ROOT = Path(
    "/media/abdullah/JARVISDATA/Knowledge"
)

FM_CANARY = (
    KNOWLEDGE_ROOT
    / "military"
    / "doctrine"
    / "US_Army_FM_3-06.11_Urban_Terrain.pdf"
)

TOKEN_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9_.+\-]{2,}"
)

STOPWORDS = {
    "the", "and", "for", "with", "from", "into",
    "this", "that", "your", "you", "are", "was",
    "were", "have", "has", "had", "not", "but",
    "all", "can", "will", "use", "using", "used",
    "book", "guide", "manual", "edition", "volume",
    "part", "file", "document", "introduction",
}


def ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=10000")

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


def fts_definition(
    conn: sqlite3.Connection,
) -> dict[str, Any]:

    row = conn.execute(
        """
        SELECT name, sql
        FROM sqlite_master
        WHERE name='runtime_chunks_fts'
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        return {
            "exists": False,
            "name": None,
            "sql": None,
            "columns": [],
        }

    return {
        "exists": True,
        "name": str(row["name"]),
        "sql": str(row["sql"] or ""),
        "columns": columns(
            conn,
            "runtime_chunks_fts",
        ),
    }


def first_existing(
    available: list[str],
    candidates: tuple[str, ...],
) -> str | None:

    aset = set(available)

    for candidate in candidates:
        if candidate in aset:
            return candidate

    return None


def discover_schema(
    conn: sqlite3.Connection,
) -> dict[str, Any]:

    required = (
        "runtime_documents",
        "runtime_chunks",
        "runtime_chunks_fts",
    )

    result: dict[str, Any] = {}

    for table in required:
        result[table] = {
            "exists":
                table_exists(conn, table),
            "columns":
                columns(conn, table),
        }

    rd_cols = result[
        "runtime_documents"
    ]["columns"]

    rc_cols = result[
        "runtime_chunks"
    ]["columns"]

    fts_cols = result[
        "runtime_chunks_fts"
    ]["columns"]

    result["mapping"] = {
        "runtime_document_id":
            first_existing(
                rd_cols,
                ("id", "document_id"),
            ),

        "runtime_document_path":
            first_existing(
                rd_cols,
                (
                    "file_path",
                    "path",
                    "source_path",
                ),
            ),

        "runtime_document_title":
            first_existing(
                rd_cols,
                (
                    "title",
                    "name",
                    "filename",
                ),
            ),

        "chunk_id":
            first_existing(
                rc_cols,
                ("id", "chunk_id"),
            ),

        "chunk_document_id":
            first_existing(
                rc_cols,
                (
                    "document_id",
                    "runtime_document_id",
                    "doc_id",
                ),
            ),

        "chunk_text":
            first_existing(
                rc_cols,
                (
                    "chunk_text",
                    "content_text",
                    "text",
                    "content",
                ),
            ),

        "fts_document_id":
            first_existing(
                fts_cols,
                (
                    "document_id",
                    "runtime_document_id",
                    "doc_id",
                ),
            ),

        "fts_chunk_id":
            first_existing(
                fts_cols,
                ("chunk_id", "id"),
            ),

        "fts_text":
            first_existing(
                fts_cols,
                (
                    "chunk_text",
                    "content_text",
                    "text",
                    "content",
                ),
            ),
    }

    return result


def clean_tokens(text: str) -> list[str]:

    tokens = []

    for match in TOKEN_RE.finditer(
        text.casefold()
    ):
        token = match.group(0).strip(
            "._+-"
        )

        if len(token) < 3:
            continue

        if token in STOPWORDS:
            continue

        if token not in tokens:
            tokens.append(token)

    return tokens


def quote_fts_token(token: str) -> str:
    token = token.replace('"', '""')
    return f'"{token}"'


def build_title_query(
    title: str,
) -> str | None:

    tokens = clean_tokens(title)

    if not tokens:
        return None

    selected = tokens[:6]

    return " AND ".join(
        quote_fts_token(token)
        for token in selected
    )


def choose_canaries(
    conn: sqlite3.Connection,
    schema: dict[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    """
    Choose only documents already proven to have chunks.

    We deliberately spread selections across the runtime ID
    range instead of taking the first N rows.
    """

    mapping = schema["mapping"]

    id_col = mapping["runtime_document_id"]
    path_col = mapping["runtime_document_path"]
    title_col = mapping["runtime_document_title"]
    chunk_doc_col = mapping["chunk_document_id"]

    if not all(
        (
            id_col,
            path_col,
            title_col,
            chunk_doc_col,
        )
    ):
        return []

    bounds = conn.execute(
        f'''
        SELECT
            MIN(rd."{id_col}") AS min_id,
            MAX(rd."{id_col}") AS max_id,
            COUNT(*) AS n
        FROM runtime_documents rd
        WHERE EXISTS (
            SELECT 1
            FROM runtime_chunks rc
            WHERE rc."{chunk_doc_col}" =
                  rd."{id_col}"
        )
        '''
    ).fetchone()

    if bounds is None:
        return []

    min_id = int(bounds["min_id"] or 0)
    max_id = int(bounds["max_id"] or 0)

    if max_id <= 0:
        return []

    if limit <= 1:
        targets = [
            min_id + (
                max_id - min_id
            ) // 2
        ]
    else:
        span = max_id - min_id

        targets = [
            min_id
            + int(
                span * i / (limit - 1)
            )
            for i in range(limit)
        ]

    selected: list[dict[str, Any]] = []
    seen: set[int] = set()

    for target in targets:

        row = conn.execute(
            f'''
            SELECT
                rd."{id_col}" AS document_id,
                rd."{path_col}" AS file_path,
                rd."{title_col}" AS title
            FROM runtime_documents rd
            WHERE rd."{id_col}" >= ?
              AND rd."{title_col}" IS NOT NULL
              AND length(
                    trim(rd."{title_col}")
                  ) >= 8
              AND EXISTS (
                    SELECT 1
                    FROM runtime_chunks rc
                    WHERE rc."{chunk_doc_col}" =
                          rd."{id_col}"
              )
            ORDER BY rd."{id_col}"
            LIMIT 1
            ''',
            (target,),
        ).fetchone()

        if row is None:
            continue

        doc_id = int(row["document_id"])

        if doc_id in seen:
            continue

        seen.add(doc_id)

        selected.append(
            {
                "document_id": doc_id,
                "file_path":
                    str(row["file_path"]),
                "title":
                    str(row["title"]),
            }
        )

    return selected[:limit]


def first_chunk_text(
    conn: sqlite3.Connection,
    schema: dict[str, Any],
    document_id: int,
) -> str | None:
    """
    Reads ONE chunk for ONE canary.

    No bulk chunk load.
    """

    mapping = schema["mapping"]

    doc_col = mapping[
        "chunk_document_id"
    ]

    text_col = mapping[
        "chunk_text"
    ]

    chunk_id_col = mapping[
        "chunk_id"
    ]

    if not doc_col or not text_col:
        return None

    order = (
        f'ORDER BY "{chunk_id_col}"'
        if chunk_id_col
        else ""
    )

    row = conn.execute(
        f'''
        SELECT "{text_col}" AS chunk_text
        FROM runtime_chunks
        WHERE "{doc_col}"=?
          AND "{text_col}" IS NOT NULL
          AND length(trim("{text_col}")) >= 80
        {order}
        LIMIT 1
        ''',
        (document_id,),
    ).fetchone()

    if row is None:
        return None

    return str(row["chunk_text"])


def build_content_probe(
    text: str | None,
) -> str | None:

    if not text:
        return None

    tokens = clean_tokens(text)

    # Prefer later tokens because the first words of books/manuals
    # often contain generic title/front-matter language.
    tokens = tokens[8:40] or tokens[:24]

    if not tokens:
        return None

    # Use up to four distinct terms.
    selected = tokens[:4]

    return " AND ".join(
        quote_fts_token(token)
        for token in selected
    )


def direct_fts_rank(
    conn: sqlite3.Connection,
    schema: dict[str, Any],
    *,
    expected_document_id: int,
    query: str | None,
    top_k: int = 20,
) -> dict[str, Any]:

    if not query:
        return {
            "query": None,
            "status": "NO_QUERY",
            "expected_rank": None,
            "top_results": [],
            "error": None,
        }

    mapping = schema["mapping"]

    fts_doc_col = mapping[
        "fts_document_id"
    ]

    fts_text_col = mapping[
        "fts_text"
    ]

    if not fts_doc_col or not fts_text_col:
        return {
            "query": query,
            "status": "FTS_SCHEMA_UNMAPPED",
            "expected_rank": None,
            "top_results": [],
            "error": None,
        }

    try:
        rows = conn.execute(
            f'''
            SELECT
                CAST(
                    "{fts_doc_col}"
                    AS INTEGER
                ) AS document_id,

                MIN(
                    bm25(runtime_chunks_fts)
                ) AS best_score

            FROM runtime_chunks_fts

            WHERE runtime_chunks_fts
                  MATCH ?

            GROUP BY
                CAST(
                    "{fts_doc_col}"
                    AS INTEGER
                )

            ORDER BY
                best_score ASC

            LIMIT ?
            ''',
            (
                query,
                top_k,
            ),
        ).fetchall()

    except sqlite3.Error as exc:
        return {
            "query": query,
            "status": "FTS_ERROR",
            "expected_rank": None,
            "top_results": [],
            "error": str(exc),
        }

    top_results = []

    expected_rank = None

    for rank, row in enumerate(
        rows,
        start=1,
    ):
        doc_id = int(
            row["document_id"]
        )

        if (
            doc_id
            == expected_document_id
            and expected_rank is None
        ):
            expected_rank = rank

        top_results.append(
            {
                "rank": rank,
                "document_id": doc_id,
                "score":
                    float(row["best_score"]),
            }
        )

    return {
        "query": query,
        "status":
            (
                "FOUND"
                if expected_rank
                is not None
                else "MISS"
            ),
        "expected_rank":
            expected_rank,
        "top_results":
            top_results,
        "error": None,
    }


def enrich_titles(
    conn: sqlite3.Connection,
    schema: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:

    mapping = schema["mapping"]

    id_col = mapping[
        "runtime_document_id"
    ]

    title_col = mapping[
        "runtime_document_title"
    ]

    if not id_col or not title_col:
        return

    for item in results:
        row = conn.execute(
            f'''
            SELECT
                "{title_col}" AS title
            FROM runtime_documents
            WHERE "{id_col}"=?
            LIMIT 1
            ''',
            (
                item["document_id"],
            ),
        ).fetchone()

        item["title"] = (
            str(row["title"])
            if row is not None
            else None
        )


def exact_title_path_rank(
    conn: sqlite3.Connection,
    schema: dict[str, Any],
    *,
    expected_document_id: int,
    title: str,
) -> dict[str, Any]:
    """
    Structured catalog-awareness control.

    This is intentionally NOT FTS. It asks whether the runtime
    catalog can identify the document directly by title.
    """

    mapping = schema["mapping"]

    id_col = mapping[
        "runtime_document_id"
    ]

    title_col = mapping[
        "runtime_document_title"
    ]

    if not id_col or not title_col:
        return {
            "status":
                "CATALOG_SCHEMA_UNMAPPED",
            "matches": [],
        }

    rows = conn.execute(
        f'''
        SELECT
            "{id_col}" AS document_id,
            "{title_col}" AS title
        FROM runtime_documents
        WHERE lower(
            trim("{title_col}")
        ) = lower(trim(?))
        ORDER BY "{id_col}"
        LIMIT 20
        ''',
        (title,),
    ).fetchall()

    matches = [
        {
            "document_id":
                int(row["document_id"]),
            "title":
                str(row["title"]),
        }
        for row in rows
    ]

    found = any(
        item["document_id"]
        == expected_document_id
        for item in matches
    )

    return {
        "status":
            (
                "FOUND"
                if found
                else "MISS"
            ),
        "matches": matches,
    }


def classify_canary(
    catalog_control: dict[str, Any],
    title_probe: dict[str, Any],
    content_probe: dict[str, Any],
) -> str:

    catalog_found = (
        catalog_control.get(
            "status"
        ) == "FOUND"
    )

    title_found = (
        title_probe.get(
            "status"
        ) == "FOUND"
    )

    content_found = (
        content_probe.get(
            "status"
        ) == "FOUND"
    )

    if not catalog_found:
        return "DOCUMENT_AWARENESS_FAILURE"

    if (
        title_probe.get("status")
        == "FTS_ERROR"
        or content_probe.get("status")
        == "FTS_ERROR"
    ):
        return "RETRIEVAL_ENGINE_ERROR"

    if not title_found and not content_found:
        return "CANDIDATE_RETRIEVAL_FAILURE"

    if content_found and (
        content_probe.get(
            "expected_rank"
        )
        or 999999
    ) > 10:
        return "RANKING_WEAKNESS"

    if title_found or content_found:
        return "DIRECT_RETRIEVAL_PASS"

    return "REVIEW"


def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--runtime-db",
        type=Path,
        default=DEFAULT_RUNTIME_DB,
    )

    parser.add_argument(
        "--json",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--canaries",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    if not args.runtime_db.is_file():
        print(
            "FAIL: runtime DB missing:",
            args.runtime_db,
            flush=True,
        )
        return 2

    if args.canaries < 1:
        print(
            "FAIL: --canaries must be >= 1",
            flush=True,
        )
        return 2

    # Keep the reconnaissance deliberately small.
    canary_limit = min(
        args.canaries,
        12,
    )

    started = time.monotonic()

    conn = ro(
        args.runtime_db
    )

    try:
        print(
            "============================================================"
        )
        print(
            " GENESIS RECALL R1B — DIRECT RETRIEVAL QUALITY"
        )
        print(
            "============================================================"
        )

        schema = discover_schema(
            conn
        )

        fts = fts_definition(
            conn
        )

        print()
        print(
            "=== 1. RETRIEVAL SCHEMA ==="
        )

        for table in (
            "runtime_documents",
            "runtime_chunks",
            "runtime_chunks_fts",
        ):
            state = schema[table]

            print(
                f"{table:24} : "
                + (
                    "PRESENT"
                    if state["exists"]
                    else "MISSING"
                )
            )

            print(
                "  columns:",
                ", ".join(
                    state["columns"]
                ),
            )

        print()
        print(
            "Mapping:"
        )

        for key, value in (
            schema["mapping"].items()
        ):
            print(
                f"  {key:24} : {value}"
            )

        print()
        print(
            "FTS definition:"
        )
        print(
            fts["sql"]
        )

        required_mapping = (
            schema["mapping"][
                "runtime_document_id"
            ],
            schema["mapping"][
                "runtime_document_title"
            ],
            schema["mapping"][
                "chunk_document_id"
            ],
            schema["mapping"][
                "chunk_text"
            ],
            schema["mapping"][
                "fts_document_id"
            ],
            schema["mapping"][
                "fts_text"
            ],
        )

        if not all(required_mapping):
            print()
            print(
                "FAIL: retrieval schema could not "
                "be mapped safely."
            )
            return 3

        print()
        print(
            "=== 2. SELECT FULLY-RUNTIME CANARIES ==="
        )

        canaries = choose_canaries(
            conn,
            schema,
            canary_limit,
        )

        if not canaries:
            print(
                "FAIL: no canaries selected"
            )
            return 4

        for canary in canaries:
            print(
                f"id={canary['document_id']:<7} "
                f"{canary['title'][:90]}"
            )

        print()
        print(
            "=== 3. DIRECT RECALL PROBES ==="
        )

        results = []

        for index, canary in enumerate(
            canaries,
            start=1,
        ):
            doc_id = canary[
                "document_id"
            ]

            title = canary[
                "title"
            ]

            print()
            print(
                f"--- CANARY {index}/{len(canaries)} ---"
            )

            print(
                "document id :",
                doc_id,
            )

            print(
                "title       :",
                title,
            )

            catalog_control = (
                exact_title_path_rank(
                    conn,
                    schema,
                    expected_document_id=
                        doc_id,
                    title=title,
                )
            )

            title_query = (
                build_title_query(
                    title
                )
            )

            title_probe = (
                direct_fts_rank(
                    conn,
                    schema,
                    expected_document_id=
                        doc_id,
                    query=title_query,
                    top_k=20,
                )
            )

            enrich_titles(
                conn,
                schema,
                title_probe[
                    "top_results"
                ],
            )

            chunk_text = (
                first_chunk_text(
                    conn,
                    schema,
                    doc_id,
                )
            )

            content_query = (
                build_content_probe(
                    chunk_text
                )
            )

            content_probe = (
                direct_fts_rank(
                    conn,
                    schema,
                    expected_document_id=
                        doc_id,
                    query=content_query,
                    top_k=20,
                )
            )

            enrich_titles(
                conn,
                schema,
                content_probe[
                    "top_results"
                ],
            )

            diagnosis = (
                classify_canary(
                    catalog_control,
                    title_probe,
                    content_probe,
                )
            )

            print(
                "catalog awareness :",
                catalog_control[
                    "status"
                ],
            )

            print(
                "title FTS query    :",
                title_query,
            )

            print(
                "title FTS result   :",
                title_probe[
                    "status"
                ],
                "rank=",
                title_probe[
                    "expected_rank"
                ],
            )

            print(
                "content FTS query  :",
                content_query,
            )

            print(
                "content FTS result :",
                content_probe[
                    "status"
                ],
                "rank=",
                content_probe[
                    "expected_rank"
                ],
            )

            print(
                "diagnosis          :",
                diagnosis,
            )

            results.append(
                {
                    **canary,
                    "catalog_control":
                        catalog_control,
                    "title_probe":
                        title_probe,
                    "content_probe":
                        content_probe,
                    "diagnosis":
                        diagnosis,
                }
            )

        print()
        print(
            "=== 4. NEGATIVE CONTROL — FM 3-06.11 ==="
        )

        fm_row = conn.execute(
            """
            SELECT
                id,
                title,
                file_path
            FROM runtime_documents
            WHERE file_path=?
            LIMIT 1
            """,
            (
                str(FM_CANARY),
            ),
        ).fetchone()

        fm_status = (
            "UNEXPECTED_RUNTIME_PRESENCE"
            if fm_row is not None
            else "PRE_RUNTIME_ASSIMILATION_GAP"
        )

        print(
            "physical      :",
            FM_CANARY.is_file(),
        )

        print(
            "runtime row   :",
            (
                dict(fm_row)
                if fm_row is not None
                else None
            ),
        )

        print(
            "control status:",
            fm_status,
        )

        print()
        print(
            "=== 5. RECALL QUALITY SUMMARY ==="
        )

        total = len(results)

        catalog_pass = sum(
            1
            for item in results
            if item[
                "catalog_control"
            ]["status"] == "FOUND"
        )

        title_top20 = sum(
            1
            for item in results
            if item[
                "title_probe"
            ]["expected_rank"] is not None
        )

        title_top5 = sum(
            1
            for item in results
            if (
                item[
                    "title_probe"
                ]["expected_rank"]
                is not None
                and item[
                    "title_probe"
                ]["expected_rank"]
                <= 5
            )
        )

        content_top20 = sum(
            1
            for item in results
            if item[
                "content_probe"
            ]["expected_rank"] is not None
        )

        content_top10 = sum(
            1
            for item in results
            if (
                item[
                    "content_probe"
                ]["expected_rank"]
                is not None
                and item[
                    "content_probe"
                ]["expected_rank"]
                <= 10
            )
        )

        content_top5 = sum(
            1
            for item in results
            if (
                item[
                    "content_probe"
                ]["expected_rank"]
                is not None
                and item[
                    "content_probe"
                ]["expected_rank"]
                <= 5
            )
        )

        diagnosis_counts: dict[str, int] = {}

        for item in results:
            diagnosis = item[
                "diagnosis"
            ]

            diagnosis_counts[
                diagnosis
            ] = (
                diagnosis_counts.get(
                    diagnosis,
                    0,
                )
                + 1
            )

        def pct(n: int) -> float:
            if total == 0:
                return 0.0

            return (
                n * 100.0 / total
            )

        print(
            f"canaries                    : {total}"
        )

        print(
            f"catalog awareness pass      : "
            f"{catalog_pass}/{total} "
            f"({pct(catalog_pass):.1f}%)"
        )

        print(
            f"title retrieval @5          : "
            f"{title_top5}/{total} "
            f"({pct(title_top5):.1f}%)"
        )

        print(
            f"title retrieval @20         : "
            f"{title_top20}/{total} "
            f"({pct(title_top20):.1f}%)"
        )

        print(
            f"content retrieval @5        : "
            f"{content_top5}/{total} "
            f"({pct(content_top5):.1f}%)"
        )

        print(
            f"content retrieval @10       : "
            f"{content_top10}/{total} "
            f"({pct(content_top10):.1f}%)"
        )

        print(
            f"content retrieval @20       : "
            f"{content_top20}/{total} "
            f"({pct(content_top20):.1f}%)"
        )

        print()
        print(
            "Diagnoses:"
        )

        for key in sorted(
            diagnosis_counts
        ):
            print(
                f"  {key:32} : "
                f"{diagnosis_counts[key]}"
            )

        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print(
            f"elapsed seconds             : {elapsed:.3f}"
        )

        print(
            "production DB writes        : 0"
        )

        report = {
            "schema":
                "genesis-recall-r1b-v1",

            "read_only":
                True,

            "retrieval_schema":
                schema,

            "fts":
                fts,

            "canaries":
                results,

            "summary": {
                "canaries":
                    total,

                "catalog_awareness_pass":
                    catalog_pass,

                "title_retrieval_at_5":
                    title_top5,

                "title_retrieval_at_20":
                    title_top20,

                "content_retrieval_at_5":
                    content_top5,

                "content_retrieval_at_10":
                    content_top10,

                "content_retrieval_at_20":
                    content_top20,

                "diagnoses":
                    diagnosis_counts,
            },

            "fm_negative_control": {
                "path":
                    str(FM_CANARY),

                "physical":
                    FM_CANARY.is_file(),

                "status":
                    fm_status,
            },

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
                    report,
                    indent=2,
                    sort_keys=True,
                    default=str,
                ),
                encoding="utf-8",
            )

            print(
                "JSON report:",
                args.json,
            )

        print()
        print(
            "GENESIS RECALL R1B DIRECT RETRIEVAL RECON: PASS"
        )

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
