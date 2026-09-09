from __future__ import annotations

import argparse
import csv
import inspect
import json
import re
import sqlite3
import time

from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA = "genesis-recall-r1g-v1"


# ============================================================
# TOKENIZATION
# ============================================================

TOKEN_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9+#._'-]{1,}"
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "onto",
    "this",
    "that",
    "these",
    "those",
    "your",
    "their",
    "our",
    "using",
    "used",
    "book",
    "books",
    "ebook",
    "ebooks",
    "guide",
    "manual",
    "edition",
    "volume",
    "volumes",
    "part",
    "file",
    "files",
    "document",
    "documents",
    "introduction",
    "complete",
    "updated",
    "final",
    "series",
    "version",
    "revised",
    "pdf",
    "txt",
    "html",
    "htm",
    "doc",
    "docx",
    "epub",
    "mobi",
    "azw",
    "azw3",
    "djvu",
    "djv",
}


def tokenize(text: str) -> list[str]:

    output: list[str] = []
    seen: set[str] = set()

    for match in TOKEN_RE.finditer(
        text or ""
    ):

        token = match.group(0).strip(
            "._'-"
        )

        if len(token) < 2:
            continue

        folded = token.casefold()

        if folded in STOPWORDS:
            continue

        if folded in seen:
            continue

        seen.add(folded)
        output.append(token)

    return output


# ============================================================
# SQLITE
# ============================================================

def ro(path: Path) -> sqlite3.Connection:

    con = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    con.execute("PRAGMA busy_timeout=10000")

    return con


def table_columns(
    con: sqlite3.Connection,
    table: str,
) -> list[str]:

    return [
        str(row["name"])
        for row in con.execute(
            f'PRAGMA table_info("{table}")'
        )
    ]


# ============================================================
# RESULT IDENTITY
# ============================================================

def result_id(row: dict[str, Any]) -> int | None:

    for key in (
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "doc_id",
        "id",
    ):

        value = row.get(key)

        if value is None:
            continue

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):
            pass

    return None


def result_path(row: dict[str, Any]) -> str:

    for key in (
        "file_path",
        "source_path",
        "document_path",
        "path",
    ):

        value = row.get(key)

        if value:
            return str(value)

    return ""


def locate(
    rows: list[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        if result_id(row) == runtime_id:
            return rank

        if (
            result_path(row)
            == expected_path
        ):
            return rank

    return None


# ============================================================
# DOCUMENT / INDEX STATE
# ============================================================

def runtime_state(
    con: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any]:

    row = con.execute(
        """
        SELECT
            id,
            title,
            file_path,
            sha256,
            media_type,
            content_chars
        FROM runtime_documents
        WHERE id=?
        LIMIT 1
        """,
        (runtime_id,),
    ).fetchone()

    if row is None:
        return {
            "runtime_present": False,
        }

    document = dict(row)

    chunks = int(
        con.execute(
            """
            SELECT COUNT(*)
            FROM runtime_chunks
            WHERE document_id=?
            """,
            (runtime_id,),
        ).fetchone()[0]
    )

    fts_rows = int(
        con.execute(
            """
            SELECT COUNT(*)
            FROM runtime_chunks_fts
            WHERE CAST(document_id AS INTEGER)=?
            """,
            (runtime_id,),
        ).fetchone()[0]
    )

    document.update(
        {
            "runtime_present":
                True,

            "chunk_count":
                chunks,

            "fts_row_count":
                fts_rows,
        }
    )

    return document


def duplicate_ids(
    con: sqlite3.Connection,
    sha256: str,
    runtime_id: int,
) -> list[int]:

    rows = con.execute(
        """
        SELECT id
        FROM runtime_documents
        WHERE sha256=?
          AND id<>?
        ORDER BY id
        LIMIT 50
        """,
        (
            sha256,
            runtime_id,
        ),
    ).fetchall()

    return [
        int(row["id"])
        for row in rows
    ]


# ============================================================
# DIRECT FTS PROBE
# ============================================================

def fts_query(
    query: str,
) -> str | None:

    terms = tokenize(query)

    if not terms:
        return None

    terms = terms[:6]

    escaped = [
        '"' + term.replace(
            '"',
            '""',
        ) + '"'
        for term in terms
    ]

    return " AND ".join(
        escaped
    )


def direct_fts(
    con: sqlite3.Connection,
    *,
    query: str,
    expected_id: int,
    limit: int = 100,
) -> dict[str, Any]:

    match = fts_query(
        query
    )

    if not match:

        return {
            "status":
                "NO_QUERY",

            "rank":
                None,

            "query":
                None,
        }

    try:

        rows = con.execute(
            """
            SELECT
                CAST(document_id AS INTEGER)
                    AS document_id,
                bm25(runtime_chunks_fts)
                    AS score
            FROM runtime_chunks_fts
            WHERE runtime_chunks_fts MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (
                match,
                limit,
            ),
        ).fetchall()

    except Exception as exc:

        return {
            "status":
                "ERROR",

            "rank":
                None,

            "query":
                match,

            "error":
                f"{type(exc).__name__}: {exc}",
        }

    seen: set[int] = set()
    doc_rank = 0

    for row in rows:

        rid = int(
            row["document_id"]
        )

        if rid in seen:
            continue

        seen.add(rid)
        doc_rank += 1

        if rid == expected_id:

            return {
                "status":
                    "FOUND",

                "rank":
                    doc_rank,

                "query":
                    match,
            }

    return {
        "status":
            "MISS",

        "rank":
            None,

        "query":
            match,
    }


# ============================================================
# CONTENT TERM COVERAGE
# ============================================================

def term_coverage(
    con: sqlite3.Connection,
    *,
    runtime_id: int,
    title: str,
    query: str,
) -> dict[str, Any]:

    query_terms = [
        token.casefold()
        for token in tokenize(
            query
        )
    ]

    title_folded = (
        title or ""
    ).casefold()

    title_hits = [
        token
        for token in query_terms
        if token in title_folded
    ]

    rows = con.execute(
        """
        SELECT chunk_text
        FROM runtime_chunks
        WHERE document_id=?
        ORDER BY id
        LIMIT 8
        """,
        (runtime_id,),
    ).fetchall()

    content = "\n".join(
        str(row["chunk_text"])
        for row in rows
    ).casefold()

    content_hits = [
        token
        for token in query_terms
        if token in content
    ]

    return {
        "query_terms":
            query_terms,

        "title_hits":
            title_hits,

        "content_hits":
            content_hits,

        "all_in_title":
            bool(
                query_terms
                and len(title_hits)
                == len(query_terms)
            ),

        "all_in_content":
            bool(
                query_terms
                and len(content_hits)
                == len(query_terms)
            ),
    }


# ============================================================
# DEEP SEARCH
# ============================================================

def deep_search(
    search_catalog: Any,
    *,
    query: str,
    db_path: Path,
    runtime_id: int,
    expected_path: str,
) -> dict[str, Any]:

    result: dict[str, Any] = {}

    for limit in (
        25,
        100,
        500,
    ):

        rows = list(
            search_catalog(
                query,
                db_path=db_path,
                limit=limit,
            )
        )

        rank = locate(
            rows,
            runtime_id=runtime_id,
            expected_path=expected_path,
        )

        result[
            str(limit)
        ] = {
            "returned":
                len(rows),

            "rank":
                rank,
        }

        if rank is not None:
            break

    return result


# ============================================================
# FAILURE CLASSIFICATION
# ============================================================

def classify_failure(
    *,
    state: dict[str, Any],
    deep: dict[str, Any],
    fts: dict[str, Any],
    coverage: dict[str, Any],
    duplicates: list[int],
    qualified_rank: int | None,
) -> str:

    if not state.get(
        "runtime_present"
    ):
        return "RUNTIME_DOCUMENT_MISSING"

    if int(
        state.get(
            "chunk_count",
            0,
        )
    ) == 0:
        return "CHUNK_INDEXING_GAP"

    if int(
        state.get(
            "fts_row_count",
            0,
        )
    ) == 0:
        return "FTS_INDEXING_GAP"

    if (
        qualified_rank is not None
        and all(
            item.get("rank")
            is None
            for item
            in deep.values()
        )
    ):
        return "QUALIFIED_PATH_DIVERGENCE"

    for limit, data in (
        deep.items()
    ):

        rank = data.get(
            "rank"
        )

        if rank is not None:

            if int(limit) > 25:
                return "CANDIDATE_HORIZON_RANKING"

            return "RAW_SEARCH_REPRODUCED"

    if (
        fts.get("status")
        == "FOUND"
    ):
        return "SEARCH_WRAPPER_SUPPRESSION"

    if duplicates:
        return "IDENTITY_DUPLICATE_AMBIGUITY"

    if not (
        coverage.get(
            "all_in_title"
        )
        or coverage.get(
            "all_in_content"
        )
    ):
        return "QUERY_DOCUMENT_LEXICAL_MISMATCH"

    if (
        fts.get("status")
        == "MISS"
    ):
        return "FTS_QUERY_MISMATCH"

    if (
        fts.get("status")
        == "ERROR"
    ):
        return "DIRECT_FTS_PROBE_ERROR"

    return "RAW_SEARCH_UNRESOLVED"


# ============================================================
# R5 QUERY ELIGIBILITY ANALYSIS
# ============================================================

def eligibility_analysis(
    con: sqlite3.Connection,
    r5_module: Any,
) -> dict[str, Any]:

    rows = con.execute(
        """
        SELECT
            id,
            title,
            media_type,
            content_chars
        FROM runtime_documents
        WHERE content_chars >= 500
          AND EXISTS (
              SELECT 1
              FROM runtime_chunks rc
              WHERE rc.document_id =
                    runtime_documents.id
          )
        ORDER BY id
        """
    ).fetchall()

    counts = Counter()

    examples: dict[
        str,
        list[dict[str, Any]],
    ] = {
        "zero_tokens": [],
        "one_token": [],
        "queryable": [],
    }

    distribution = Counter()

    for row in rows:

        title = str(
            row["title"]
            or ""
        )

        terms = r5_module.tokenize(
            title
        )

        query = r5_module.build_query(
            title
        )

        distribution[
            str(
                min(
                    len(terms),
                    5,
                )
            )
        ] += 1

        if len(terms) == 0:

            bucket = "zero_tokens"

        elif len(terms) == 1:

            bucket = "one_token"

        elif query:

            bucket = "queryable"

        else:

            bucket = "other_unusable"

        counts[
            bucket
        ] += 1

        if (
            bucket in examples
            and len(
                examples[bucket]
            ) < 25
        ):

            examples[
                bucket
            ].append(
                {
                    "id":
                        int(
                            row["id"]
                        ),

                    "title":
                        title,

                    "tokens":
                        terms,

                    "query":
                        query,
                }
            )

    return {
        "total":
            len(rows),

        "counts":
            dict(counts),

        "token_count_distribution":
            dict(distribution),

        "examples":
            examples,
    }


# ============================================================
# MAIN
# ============================================================

def main() -> int:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--r5-report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--failure-tsv",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--eligibility-tsv",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    from core.knowledge_catalog.search import (
        search_catalog,
    )

    from core.knowledge_catalog.qualified_search import (
        search_qualified_catalog,
    )

    import dev.recall.r1f_r5_recall_census as r5


    started = time.monotonic()

    r5_report = json.loads(
        args.r5_report.read_text(
            encoding="utf-8"
        )
    )

    cases = [
        item
        for item
        in r5_report.get(
            "results",
            []
        )
        if (
            item.get(
                "status"
            )
            == "RAW_RETRIEVAL_MISS"
            or (
                item.get(
                    "raw_rank"
                )
                is None
                and item.get(
                    "qualified_rank"
                )
                is not None
            )
        )
    ]

    con = ro(
        args.db
    )


    try:

        print(
            "============================================================"
        )

        print(
            " GENESIS RECALL R1G"
        )

        print(
            " RAW RETRIEVAL FAILURE ANATOMY"
        )

        print(
            "============================================================"
        )


        # ====================================================
        # 1. SEARCH IMPLEMENTATION CONTRACT
        # ====================================================

        print()
        print(
            "=== 1. PRODUCTION SEARCH CONTRACT ==="
        )

        print(
            "search_catalog:",
            inspect.signature(
                search_catalog
            ),
        )

        print(
            "search_qualified_catalog:",
            inspect.signature(
                search_qualified_catalog
            ),
        )

        print()
        print(
            "--- search_catalog source ---"
        )

        try:

            print(
                inspect.getsource(
                    search_catalog
                )
            )

        except Exception as exc:

            print(
                "SOURCE UNAVAILABLE:",
                exc,
            )


        # ====================================================
        # 2. FTS SCHEMA
        # ====================================================

        print()
        print(
            "=== 2. RUNTIME SEARCH SCHEMA ==="
        )

        for table in (
            "runtime_documents",
            "runtime_chunks",
            "runtime_chunks_fts",
        ):

            cols = table_columns(
                con,
                table,
            )

            print(
                table,
                ":",
                ", ".join(cols),
            )


        # ====================================================
        # 3. RAW FAILURE ANATOMY
        # ====================================================

        print()
        print(
            "=== 3. R5 RAW FAILURE CASES ==="
        )

        print(
            "cases:",
            len(cases),
        )

        anatomy: list[
            dict[str, Any]
        ] = []

        classes = Counter()

        for number, case in enumerate(
            cases,
            start=1,
        ):

            runtime_id = int(
                case[
                    "runtime_id"
                ]
            )

            query = str(
                case[
                    "query"
                ]
            )

            expected_path = str(
                case[
                    "file_path"
                ]
            )

            state = runtime_state(
                con,
                runtime_id,
            )

            if not state.get(
                "runtime_present"
            ):

                title = str(
                    case.get(
                        "title"
                    )
                    or ""
                )

                duplicates = []
                coverage = {}
                fts = {
                    "status":
                        "NOT_RUN",
                }

                deep = {}

            else:

                title = str(
                    state[
                        "title"
                    ]
                )

                duplicates = duplicate_ids(
                    con,
                    str(
                        state[
                            "sha256"
                        ]
                    ),
                    runtime_id,
                )

                coverage = term_coverage(
                    con,
                    runtime_id=
                        runtime_id,
                    title=title,
                    query=query,
                )

                fts = direct_fts(
                    con,
                    query=query,
                    expected_id=
                        runtime_id,
                    limit=100,
                )

                deep = deep_search(
                    search_catalog,
                    query=query,
                    db_path=args.db,
                    runtime_id=
                        runtime_id,
                    expected_path=
                        expected_path,
                )

            qualified_rows = list(
                search_qualified_catalog(
                    query,
                    db_path=args.db,
                    limit=100,
                )
            )

            qualified_rank = locate(
                qualified_rows,
                runtime_id=
                    runtime_id,
                expected_path=
                    expected_path,
            )

            classification = (
                classify_failure(
                    state=state,
                    deep=deep,
                    fts=fts,
                    coverage=coverage,
                    duplicates=
                        duplicates,
                    qualified_rank=
                        qualified_rank,
                )
            )

            classes[
                classification
            ] += 1

            record = {
                "sample_number":
                    case.get(
                        "sample_number"
                    ),

                "runtime_id":
                    runtime_id,

                "title":
                    title,

                "query":
                    query,

                "r5_raw_rank":
                    case.get(
                        "raw_rank"
                    ),

                "r5_qualified_rank":
                    case.get(
                        "qualified_rank"
                    ),

                "rerun_qualified_rank":
                    qualified_rank,

                "state":
                    state,

                "duplicate_runtime_ids":
                    duplicates,

                "coverage":
                    coverage,

                "direct_fts":
                    fts,

                "deep_search":
                    deep,

                "classification":
                    classification,
            }

            anatomy.append(
                record
            )

            print()
            print(
                "------------------------------------------------------------"
            )

            print(
                f"[{number:02d}/{len(cases):02d}] "
                f"id={runtime_id}"
            )

            print(
                "title          :",
                title,
            )

            print(
                "query          :",
                query,
            )

            print(
                "chunks         :",
                state.get(
                    "chunk_count"
                ),
            )

            print(
                "FTS rows       :",
                state.get(
                    "fts_row_count"
                ),
            )

            print(
                "duplicates     :",
                duplicates,
            )

            print(
                "title coverage :",
                coverage.get(
                    "title_hits"
                ),
            )

            print(
                "chunk coverage :",
                coverage.get(
                    "content_hits"
                ),
            )

            print(
                "direct FTS     :",
                fts.get(
                    "status"
                ),
                "rank=",
                fts.get(
                    "rank"
                ),
            )

            print(
                "search@25      :",
                (
                    deep.get(
                        "25",
                        {}
                    ).get(
                        "rank"
                    )
                ),
            )

            print(
                "search@100     :",
                (
                    deep.get(
                        "100",
                        {}
                    ).get(
                        "rank"
                    )
                ),
            )

            print(
                "search@500     :",
                (
                    deep.get(
                        "500",
                        {}
                    ).get(
                        "rank"
                    )
                ),
            )

            print(
                "qualified@100  :",
                qualified_rank,
            )

            print(
                "CLASSIFICATION :",
                classification,
            )


        # ====================================================
        # 4. CLASSIFICATION SUMMARY
        # ====================================================

        print()
        print(
            "=== 4. RAW FAILURE CLASSIFICATION ==="
        )

        for name, count in (
            classes.most_common()
        ):

            print(
                f"{name:38} : {count}"
            )


        # ====================================================
        # 5. PATH DIVERGENCE
        # ====================================================

        print()
        print(
            "=== 5. RAW / QUALIFIED PATH DIVERGENCE ==="
        )

        divergences = [
            item
            for item
            in anatomy
            if (
                item[
                    "r5_raw_rank"
                ]
                is None
                and (
                    item[
                        "r5_qualified_rank"
                    ]
                    is not None
                    or item[
                        "rerun_qualified_rank"
                    ]
                    is not None
                )
            )
        ]

        print(
            "divergent cases:",
            len(divergences),
        )

        for item in divergences:

            print(
                "  id=",
                item[
                    "runtime_id"
                ],
                " R5 qualified=",
                item[
                    "r5_qualified_rank"
                ],
                " rerun qualified=",
                item[
                    "rerun_qualified_rank"
                ],
                " class=",
                item[
                    "classification"
                ],
                sep="",
            )


        # ====================================================
        # 6. R5 QUERY ELIGIBILITY ANATOMY
        # ====================================================

        print()
        print(
            "=== 6. R5 QUERY ELIGIBILITY ANATOMY ==="
        )

        eligibility = (
            eligibility_analysis(
                con,
                r5,
            )
        )

        print(
            "chunked/content documents :",
            eligibility[
                "total"
            ],
        )

        for key, value in (
            sorted(
                eligibility[
                    "counts"
                ].items()
            )
        ):

            print(
                f"{key:24} : {value}"
            )

        print()
        print(
            "token-count distribution:"
        )

        for key, value in sorted(
            eligibility[
                "token_count_distribution"
            ].items(),
            key=lambda item:
                int(item[0]),
        ):

            label = (
                "5+"
                if key == "5"
                else key
            )

            print(
                f"  tokens={label:>2} : "
                f"{value}"
            )

        print()
        print(
            "one-token title examples:"
        )

        for item in (
            eligibility[
                "examples"
            ][
                "one_token"
            ][
                :20
            ]
        ):

            print(
                f"  id={item['id']} "
                f"title={item['title']!r} "
                f"tokens={item['tokens']}"
            )


        # ====================================================
        # 7. WRITE TSVs
        # ====================================================

        args.failure_tsv.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with args.failure_tsv.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:

            fields = (
                "sample_number",
                "runtime_id",
                "classification",
                "r5_raw_rank",
                "r5_qualified_rank",
                "rerun_qualified_rank",
                "query",
                "title",
                "chunk_count",
                "fts_row_count",
                "direct_fts_status",
                "direct_fts_rank",
                "duplicate_runtime_ids",
            )

            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
                delimiter="\t",
            )

            writer.writeheader()

            for item in anatomy:

                state = (
                    item.get(
                        "state"
                    )
                    or {}
                )

                fts = (
                    item.get(
                        "direct_fts"
                    )
                    or {}
                )

                writer.writerow(
                    {
                        "sample_number":
                            item.get(
                                "sample_number"
                            ),

                        "runtime_id":
                            item[
                                "runtime_id"
                            ],

                        "classification":
                            item[
                                "classification"
                            ],

                        "r5_raw_rank":
                            item[
                                "r5_raw_rank"
                            ],

                        "r5_qualified_rank":
                            item[
                                "r5_qualified_rank"
                            ],

                        "rerun_qualified_rank":
                            item[
                                "rerun_qualified_rank"
                            ],

                        "query":
                            item[
                                "query"
                            ],

                        "title":
                            item[
                                "title"
                            ],

                        "chunk_count":
                            state.get(
                                "chunk_count"
                            ),

                        "fts_row_count":
                            state.get(
                                "fts_row_count"
                            ),

                        "direct_fts_status":
                            fts.get(
                                "status"
                            ),

                        "direct_fts_rank":
                            fts.get(
                                "rank"
                            ),

                        "duplicate_runtime_ids":
                            ",".join(
                                str(value)
                                for value
                                in item[
                                    "duplicate_runtime_ids"
                                ]
                            ),
                    }
                )


        with args.eligibility_tsv.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:

            fields = (
                "bucket",
                "runtime_id",
                "title",
                "tokens",
                "query",
            )

            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
                delimiter="\t",
            )

            writer.writeheader()

            for bucket, examples in (
                eligibility[
                    "examples"
                ].items()
            ):

                for item in examples:

                    writer.writerow(
                        {
                            "bucket":
                                bucket,

                            "runtime_id":
                                item[
                                    "id"
                                ],

                            "title":
                                item[
                                    "title"
                                ],

                            "tokens":
                                " | ".join(
                                    item[
                                        "tokens"
                                    ]
                                ),

                            "query":
                                item[
                                    "query"
                                ],
                        }
                    )


        # ====================================================
        # 8. REPORT
        # ====================================================

        elapsed = (
            time.monotonic()
            - started
        )

        report = {
            "schema":
                SCHEMA,

            "read_only":
                True,

            "r5_failure_cases":
                len(cases),

            "classification_counts":
                dict(classes),

            "failures":
                anatomy,

            "divergences":
                divergences,

            "query_eligibility":
                eligibility,

            "elapsed_seconds":
                elapsed,
        }

        args.report.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        args.report.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=True,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )


        # ====================================================
        # 9. FINAL
        # ====================================================

        print()
        print(
            "============================================================"
        )

        print(
            " JARVIS RAW RETRIEVAL FAILURE ANATOMY"
        )

        print(
            "============================================================"
        )

        print(
            "R5 failure cases analyzed :",
            len(cases),
        )

        print(
            "raw/qualified divergences :",
            len(divergences),
        )

        print()
        print(
            "Failure classes:"
        )

        for name, count in (
            classes.most_common()
        ):

            print(
                f"  {name:38} : "
                f"{count}"
            )

        print()
        print(
            "Benchmark query eligibility:"
        )

        print(
            "  chunked/content universe :",
            eligibility[
                "total"
            ],
        )

        for key, value in sorted(
            eligibility[
                "counts"
            ].items()
        ):

            print(
                f"  {key:24} : "
                f"{value}"
            )

        print()
        print(
            f"elapsed seconds           : "
            f"{elapsed:.2f}"
        )

        print(
            "production DB writes      : 0"
        )

        print(
            "production source changes : 0"
        )

        print()
        print(
            "JSON report:",
            args.report,
        )

        print(
            "Failure TSV:",
            args.failure_tsv,
        )

        print(
            "Eligibility TSV:",
            args.eligibility_tsv,
        )

        print(
            "============================================================"
        )

        return 0


    finally:

        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
