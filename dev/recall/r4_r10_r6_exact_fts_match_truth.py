from __future__ import annotations

import csv
import inspect
import json
import math
import re
import sqlite3
import sys
import time

from collections import Counter
from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

DETAIL_IN = (
    OUTDIR
    / "r4_r10_r5_runtime_search_anatomy.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r6_exact_fts_match_truth.json"
)

DETAIL = (
    OUTDIR
    / "r4_r10_r6_exact_fts_match_truth.tsv"
)

VARIANTS = (
    OUTDIR
    / "r4_r10_r6_query_variant_anatomy.tsv"
)

TERMS = (
    OUTDIR
    / "r4_r10_r6_term_contribution.tsv"
)

TARGET_CHUNKS = (
    OUTDIR
    / "r4_r10_r6_target_chunk_ranks.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_r6_fts_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r6_fts_source_contract.txt"
)


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.materialization.search import (
    _fts_query,
    _confidence,
    search_runtime_knowledge,
)


EXPECTED = 9

EXPECTED_R5_CLASSES = {
    "SQL_MATCH_LOW_RANK": 7,
    "SQL_QUERY_DID_NOT_MATCH_TARGET": 2,
}


# ============================================================
# HELPERS
# ============================================================

def read_tsv(path: Path) -> list[dict[str, str]]:

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        return list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )


def write_tsv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:

    if not rows:
        path.write_text(
            "",
            encoding="utf-8",
        )
        return

    fields = []
    seen = set()

    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def qterms_from_fts(
    expression: str,
) -> tuple[str, ...]:

    return tuple(
        re.findall(
            r'"([^"]+)"',
            expression or "",
        )
    )


def quoted(term: str) -> str:

    safe = (
        str(term)
        .replace('"', '""')
        .strip()
    )

    return f'"{safe}"'


def make_or(
    terms: tuple[str, ...],
) -> str:

    return " OR ".join(
        quoted(term)
        for term in terms
        if term
    )


def make_and(
    terms: tuple[str, ...],
) -> str:

    return " AND ".join(
        quoted(term)
        for term in terms
        if term
    )


def title_terms(
    title: str,
) -> tuple[str, ...]:

    seen = set()
    result = []

    for token in re.findall(
        r"[A-Za-z0-9_]{2,}",
        str(title or "").casefold(),
    ):

        if token in seen:
            continue

        seen.add(token)
        result.append(token)

    return tuple(result)


def title_boundary_terms(
    title: str,
) -> tuple[str, ...]:

    seen = set()
    result = []

    # Deliberately diagnostic only:
    # split punctuation/underscore boundaries more aggressively.
    for token in re.findall(
        r"[A-Za-z0-9]{2,}",
        str(title or "").casefold(),
    ):

        if token in seen:
            continue

        seen.add(token)
        result.append(token)

    return tuple(result)


def scalar(value: Any) -> str:

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# READ-ONLY DATABASE
# ============================================================

conn = sqlite3.connect(
    f"file:{DB}?mode=ro",
    uri=True,
)

conn.row_factory = sqlite3.Row

conn.execute(
    "PRAGMA query_only=ON"
)

integrity = conn.execute(
    "PRAGMA integrity_check"
).fetchone()[0]

if integrity != "ok":
    raise RuntimeError(
        f"database integrity failure: {integrity}"
    )


fts_exists = (
    conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE name='runtime_chunks_fts'
        """
    ).fetchone()
    is not None
)

if not fts_exists:
    raise RuntimeError(
        "runtime_chunks_fts unavailable"
    )


# ============================================================
# TARGET DOCUMENT INFO
# ============================================================

def document_info(
    document_id: str,
) -> dict[str, Any]:

    row = conn.execute(
        """
        SELECT
            id,
            title,
            file_path
        FROM runtime_documents
        WHERE id = ?
        """,
        (
            int(document_id),
        ),
    ).fetchone()

    if row is None:
        raise RuntimeError(
            f"runtime document missing: {document_id}"
        )

    count = conn.execute(
        """
        SELECT COUNT(*)
        FROM runtime_chunks
        WHERE document_id = ?
        """,
        (
            int(document_id),
        ),
    ).fetchone()[0]

    return {
        "id":
            int(row["id"]),

        "title":
            scalar(row["title"]),

        "file_path":
            scalar(row["file_path"]),

        "chunk_count":
            int(count),
    }


# ============================================================
# UNLIMITED FTS SCAN
# ============================================================
#
# FTS5 bm25() is most reliable in the MATCH SELECT itself.
# Rather than trying to reference bm25() inside a nested WHERE,
# stream the ordered complete match population once and compute
# exact target positions directly.
# ============================================================

def scan_match_population(
    expression: str,
    target_document_id: int,
) -> dict[str, Any]:

    if not expression.strip():

        return {
            "valid":
                False,

            "match_count":
                0,

            "target_match":
                False,

            "best_target_rank":
                None,

            "best_target_bm25":
                None,

            "best_target_chunk":
                None,

            "target_match_count":
                0,

            "target_chunks":
                [],
        }


    cursor = conn.execute(
        """
        SELECT
            f.chunk_id,
            f.document_id,
            f.title,
            f.file_path,
            bm25(runtime_chunks_fts) AS rank
        FROM runtime_chunks_fts f
        WHERE runtime_chunks_fts MATCH ?
        ORDER BY rank
        """,
        (
            expression,
        ),
    )


    ordinal = 0
    target_chunks = []


    while True:

        batch = cursor.fetchmany(
            4096
        )

        if not batch:
            break


        for row in batch:

            ordinal += 1

            if int(
                row["document_id"]
            ) != int(
                target_document_id
            ):
                continue

            target_chunks.append(
                {
                    "global_rank":
                        ordinal,

                    "chunk_id":
                        int(
                            row["chunk_id"]
                        ),

                    "bm25":
                        float(
                            row["rank"]
                            or 0.0
                        ),
                }
            )


    best = (
        target_chunks[0]
        if target_chunks
        else None
    )


    return {
        "valid":
            True,

        "match_count":
            ordinal,

        "target_match":
            bool(
                target_chunks
            ),

        "best_target_rank":
            (
                best[
                    "global_rank"
                ]
                if best
                else None
            ),

        "best_target_bm25":
            (
                best[
                    "bm25"
                ]
                if best
                else None
            ),

        "best_target_chunk":
            (
                best[
                    "chunk_id"
                ]
                if best
                else None
            ),

        "target_match_count":
            len(
                target_chunks
            ),

        "target_chunks":
            target_chunks,
    }


# ============================================================
# QUERY VARIANTS
# ============================================================

def variants_for(
    query: str,
    title: str,
) -> list[tuple[str, str]]:

    production = _fts_query(
        query
    )

    prod_terms = qterms_from_fts(
        production
    )


    no_html = tuple(
        term
        for term in prod_terms
        if term.casefold()
        not in {
            "html",
            "htm",
        }
    )


    no_numeric = tuple(
        term
        for term in prod_terms
        if not term.isdigit()
    )


    substantive = tuple(
        term
        for term in prod_terms
        if term.casefold()
        not in {
            "html",
            "htm",
        }
        and
        not (
            term.isdigit()
            and
            len(term) <= 2
        )
    )


    title_native = title_terms(
        title
    )

    title_boundary = title_boundary_terms(
        title
    )


    rows = [
        (
            "PRODUCTION_OR",
            production,
        ),
        (
            "PRODUCTION_TERMS_AND",
            make_and(
                prod_terms
            ),
        ),
        (
            "NO_HTML_OR",
            make_or(
                no_html
            ),
        ),
        (
            "NO_HTML_AND",
            make_and(
                no_html
            ),
        ),
        (
            "NO_NUMERIC_OR",
            make_or(
                no_numeric
            ),
        ),
        (
            "SUBSTANTIVE_AND",
            make_and(
                substantive
            ),
        ),
        (
            "TITLE_NATIVE_OR",
            make_or(
                title_native
            ),
        ),
        (
            "TITLE_NATIVE_AND",
            make_and(
                title_native
            ),
        ),
        (
            "TITLE_BOUNDARY_OR",
            make_or(
                title_boundary
            ),
        ),
        (
            "TITLE_BOUNDARY_AND",
            make_and(
                title_boundary
            ),
        ),
    ]


    # Stable dedup by exact expression.
    result = []
    seen = set()

    for name, expression in rows:

        key = expression.strip()

        if not key:
            continue

        pair = (
            name,
            key,
        )

        if pair in seen:
            continue

        seen.add(pair)

        result.append(
            (
                name,
                key,
            )
        )

    return result


# ============================================================
# LOAD R5 POPULATION
# ============================================================

targets = read_tsv(
    DETAIL_IN
)

if len(targets) != EXPECTED:
    raise RuntimeError(
        f"expected 9 R5 targets, got {len(targets)}"
    )


r5_classes = Counter(
    row[
        "anatomy_class"
    ]
    for row in targets
)

if dict(r5_classes) != EXPECTED_R5_CLASSES:
    raise RuntimeError(
        f"unexpected R5 classes: {dict(r5_classes)}"
    )


# ============================================================
# RUN
# ============================================================

started = time.time()

detail_rows = []
variant_rows = []
term_rows = []
chunk_rows = []
trace_lines = []

root_classes = Counter()

production_matches = 0
production_no_matches = 0
production_beyond_2000 = 0
production_within_2000 = 0

r5_rank_parity = 0
r5_rank_mismatch = 0


for case, item in enumerate(
    targets,
    start=1,
):

    document_id = str(
        item[
            "document_id"
        ]
    )

    query = item[
        "query"
    ]

    r5_class = item[
        "anatomy_class"
    ]


    doc = document_info(
        document_id
    )


    production_expression = _fts_query(
        query
    )

    production_terms = qterms_from_fts(
        production_expression
    )


    production_scan = scan_match_population(
        production_expression,
        doc["id"],
    )


    # --------------------------------------------------------
    # R5 observed rank parity
    # --------------------------------------------------------

    r5_rank_raw = item.get(
        "target_final_rank",
        "",
    ).strip()

    r5_rank = (
        int(r5_rank_raw)
        if r5_rank_raw
        else None
    )


    unlimited_rank = production_scan[
        "best_target_rank"
    ]


    if production_scan[
        "target_match"
    ]:

        production_matches += 1

        if unlimited_rank is not None:

            if unlimited_rank > 2000:
                production_beyond_2000 += 1
            else:
                production_within_2000 += 1


        if (
            r5_rank is not None
            and
            unlimited_rank == r5_rank
        ):
            r5_rank_parity += 1

        elif (
            r5_rank is not None
            and
            unlimited_rank != r5_rank
        ):
            r5_rank_mismatch += 1

    else:

        production_no_matches += 1


    # --------------------------------------------------------
    # Controlled variants
    # --------------------------------------------------------

    case_variant_rows = []


    for variant_name, expression in variants_for(
        query,
        doc["title"],
    ):

        try:

            scan = scan_match_population(
                expression,
                doc["id"],
            )

            status = "OK"

        except sqlite3.OperationalError as exc:

            scan = {
                "valid":
                    False,

                "match_count":
                    0,

                "target_match":
                    False,

                "best_target_rank":
                    None,

                "best_target_bm25":
                    None,

                "best_target_chunk":
                    None,

                "target_match_count":
                    0,

                "target_chunks":
                    [],
            }

            status = (
                "FTS_ERROR:"
                + str(exc)
            )


        variant_row = {
            "case":
                case,

            "document_id":
                document_id,

            "query":
                query,

            "title":
                doc["title"],

            "variant":
                variant_name,

            "fts_expression":
                expression,

            "total_matches":
                scan[
                    "match_count"
                ],

            "target_matches":
                scan[
                    "target_match_count"
                ],

            "target_match":
                scan[
                    "target_match"
                ],

            "target_best_rank":
                (
                    scan[
                        "best_target_rank"
                    ]
                    if scan[
                        "best_target_rank"
                    ]
                    is not None
                    else ""
                ),

            "target_best_bm25":
                (
                    scan[
                        "best_target_bm25"
                    ]
                    if scan[
                        "best_target_bm25"
                    ]
                    is not None
                    else ""
                ),

            "target_best_chunk":
                (
                    scan[
                        "best_target_chunk"
                    ]
                    if scan[
                        "best_target_chunk"
                    ]
                    is not None
                    else ""
                ),

            "status":
                status,
        }


        variant_rows.append(
            variant_row
        )

        case_variant_rows.append(
            variant_row
        )


        for target_chunk in scan[
            "target_chunks"
        ]:

            chunk_rows.append(
                {
                    "case":
                        case,

                    "document_id":
                        document_id,

                    "variant":
                        variant_name,

                    "chunk_id":
                        target_chunk[
                            "chunk_id"
                        ],

                    "global_rank":
                        target_chunk[
                            "global_rank"
                        ],

                    "bm25":
                        target_chunk[
                            "bm25"
                        ],
                }
            )


    # --------------------------------------------------------
    # Per-term contribution
    # --------------------------------------------------------

    per_term = []


    for term in production_terms:

        expression = quoted(
            term
        )

        try:

            scan = scan_match_population(
                expression,
                doc["id"],
            )

            status = "OK"

        except sqlite3.OperationalError as exc:

            scan = {
                "match_count":
                    0,

                "target_match":
                    False,

                "best_target_rank":
                    None,

                "best_target_bm25":
                    None,

                "best_target_chunk":
                    None,

                "target_match_count":
                    0,
            }

            status = (
                "FTS_ERROR:"
                + str(exc)
            )


        term_row = {
            "case":
                case,

            "document_id":
                document_id,

            "query":
                query,

            "term":
                term,

            "fts_expression":
                expression,

            "global_match_count":
                scan[
                    "match_count"
                ],

            "target_match":
                scan[
                    "target_match"
                ],

            "target_match_count":
                scan[
                    "target_match_count"
                ],

            "target_best_rank":
                (
                    scan[
                        "best_target_rank"
                    ]
                    if scan[
                        "best_target_rank"
                    ]
                    is not None
                    else ""
                ),

            "target_best_bm25":
                (
                    scan[
                        "best_target_bm25"
                    ]
                    if scan[
                        "best_target_bm25"
                    ]
                    is not None
                    else ""
                ),

            "status":
                status,
        }


        term_rows.append(
            term_row
        )

        per_term.append(
            term_row
        )


    # --------------------------------------------------------
    # Root-cause classification
    # --------------------------------------------------------

    variant_by_name = {
        row[
            "variant"
        ]:
            row
        for row in case_variant_rows
    }


    prod = variant_by_name.get(
        "PRODUCTION_OR",
        {}
    )

    no_html = variant_by_name.get(
        "NO_HTML_OR",
        {}
    )

    prod_and = variant_by_name.get(
        "PRODUCTION_TERMS_AND",
        {}
    )

    title_and = variant_by_name.get(
        "TITLE_BOUNDARY_AND",
        {},
    )


    matched_terms = [
        row
        for row in per_term
        if row[
            "target_match"
        ]
        in (
            True,
            "True",
        )
    ]


    generic_heavy = False

    if production_terms:

        global_counts = [
            (
                row[
                    "term"
                ],
                int(
                    row[
                        "global_match_count"
                    ]
                    or 0
                ),
            )
            for row in per_term
        ]

        if global_counts:

            largest_term, largest_count = max(
                global_counts,
                key=lambda pair:
                    pair[1],
            )

            generic_heavy = (
                largest_count
                > 5000
                or
                largest_term
                in {
                    "html",
                    "action",
                    "enemy",
                    "meeting",
                    "security",
                }
            )


    if not production_scan[
        "target_match"
    ]:

        if matched_terms:

            root_class = (
                "OR_QUERY_TARGET_UNION_ANOMALY"
            )

        elif title_and.get(
            "target_match"
        ) in (
            True,
            "True",
        ):

            root_class = (
                "TOKENIZATION_IDENTITY_DIVERGENCE"
            )

        else:

            root_class = (
                "TRUE_FTS_NO_MATCH"
            )


    elif unlimited_rank is not None and unlimited_rank > 2000:

        root_class = (
            "MATCHED_BEYOND_2000"
        )


    elif (
        no_html
        and
        no_html.get(
            "target_match"
        )
        in (
            True,
            "True",
        )
        and
        no_html.get(
            "target_best_rank"
        )
        not in (
            "",
            None,
        )
        and
        unlimited_rank is not None
        and
        int(
            no_html[
                "target_best_rank"
            ]
        )
        < unlimited_rank
        * 0.5
    ):

        root_class = (
            "OR_QUERY_GENERIC_TERM_DOMINANCE"
        )


    elif (
        prod_and
        and
        prod_and.get(
            "target_match"
        )
        in (
            True,
            "True",
        )
        and
        prod_and.get(
            "target_best_rank"
        )
        not in (
            "",
            None,
        )
        and
        unlimited_rank is not None
        and
        int(
            prod_and[
                "target_best_rank"
            ]
        )
        <= max(
            100,
            int(
                unlimited_rank
                * 0.25
            ),
        )
    ):

        root_class = (
            "OR_QUERY_GENERIC_TERM_DOMINANCE"
        )


    elif generic_heavy:

        root_class = (
            "GENERIC_TERM_DOMINANCE"
        )


    elif (
        title_and
        and
        title_and.get(
            "target_match"
        )
        in (
            True,
            "True",
        )
        and
        title_and.get(
            "target_best_rank"
        )
        not in (
            "",
            None,
        )
        and
        unlimited_rank is not None
        and
        int(
            title_and[
                "target_best_rank"
            ]
        )
        < unlimited_rank
    ):

        root_class = (
            "TITLE_IDENTITY_UNDERWEIGHTED"
        )


    else:

        root_class = (
            "BM25_OR_QUERY_RANKING_WEAKNESS"
        )


    root_classes[
        root_class
    ] += 1


    confidence = ""

    if (
        production_scan[
            "best_target_bm25"
        ]
        is not None
        and
        unlimited_rank is not None
    ):

        confidence = _confidence(
            float(
                production_scan[
                    "best_target_bm25"
                ]
            ),
            int(
                unlimited_rank
                - 1
            ),
        )


    detail_rows.append(
        {
            "case":
                case,

            "document_id":
                document_id,

            "query":
                query,

            "title":
                doc[
                    "title"
                ],

            "chunk_count":
                doc[
                    "chunk_count"
                ],

            "r5_class":
                r5_class,

            "production_fts_query":
                production_expression,

            "production_terms":
                ",".join(
                    production_terms
                ),

            "production_total_matches":
                production_scan[
                    "match_count"
                ],

            "production_target_match":
                production_scan[
                    "target_match"
                ],

            "production_target_chunk_matches":
                production_scan[
                    "target_match_count"
                ],

            "production_target_best_rank":
                (
                    unlimited_rank
                    if unlimited_rank
                    is not None
                    else ""
                ),

            "production_target_best_bm25":
                (
                    production_scan[
                        "best_target_bm25"
                    ]
                    if production_scan[
                        "best_target_bm25"
                    ]
                    is not None
                    else ""
                ),

            "production_target_best_chunk":
                (
                    production_scan[
                        "best_target_chunk"
                    ]
                    if production_scan[
                        "best_target_chunk"
                    ]
                    is not None
                    else ""
                ),

            "derived_confidence":
                confidence,

            "r5_observed_rank":
                (
                    r5_rank
                    if r5_rank
                    is not None
                    else ""
                ),

            "r5_unlimited_rank_parity":
                (
                    r5_rank == unlimited_rank
                    if r5_rank is not None
                    else ""
                ),

            "matched_terms":
                ",".join(
                    row[
                        "term"
                    ]
                    for row in matched_terms
                ),

            "root_class":
                root_class,
        }
    )


    trace_lines.extend(
        (
            "=" * 78,
            f"CASE {case:02d}",
            "=" * 78,
            f"document_id          : {document_id}",
            f"query                : {query}",
            f"title                : {doc['title']}",
            f"R5 class             : {r5_class}",
            "",
            f"production FTS       : {production_expression}",
            f"production terms     : {production_terms}",
            f"total FTS matches    : {production_scan['match_count']}",
            f"target matches       : {production_scan['target_match']}",
            f"target chunk matches : {production_scan['target_match_count']}",
            f"best target rank     : {unlimited_rank}",
            f"best target BM25     : {production_scan['best_target_bm25']}",
            f"best target chunk    : {production_scan['best_target_chunk']}",
            f"R5 observed rank     : {r5_rank}",
            "",
            f"matched individual terms:"
            f" {[row['term'] for row in matched_terms]}",
            "",
            f"ROOT CLASS           : {root_class}",
            "",
            "QUERY VARIANTS",
        )
    )


    for row in case_variant_rows:

        trace_lines.append(
            "  "
            + json.dumps(
                {
                    "variant":
                        row[
                            "variant"
                        ],

                    "expression":
                        row[
                            "fts_expression"
                        ],

                    "total_matches":
                        row[
                            "total_matches"
                        ],

                    "target_match":
                        row[
                            "target_match"
                        ],

                    "target_rank":
                        row[
                            "target_best_rank"
                        ],

                    "target_bm25":
                        row[
                            "target_best_bm25"
                        ],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
        )


    trace_lines.extend(
        (
            "",
            "TERM CONTRIBUTIONS",
        )
    )


    for row in per_term:

        trace_lines.append(
            "  "
            + json.dumps(
                {
                    "term":
                        row[
                            "term"
                        ],

                    "global_matches":
                        row[
                            "global_match_count"
                        ],

                    "target_match":
                        row[
                            "target_match"
                        ],

                    "target_rank":
                        row[
                            "target_best_rank"
                        ],

                    "target_bm25":
                        row[
                            "target_best_bm25"
                        ],
                },
                sort_keys=True,
                ensure_ascii=False,
            )
        )


    trace_lines.append(
        ""
    )


# ============================================================
# CERTIFICATION
# ============================================================

all_exact_population = (
    len(
        detail_rows
    )
    == EXPECTED
)


all_production_truth_known = all(
    row[
        "production_target_match"
    ]
    in (
        True,
        False,
    )
    for row in detail_rows
)


all_root_classified = all(
    row[
        "root_class"
    ]
    not in (
        "",
        "OTHER",
    )
    for row in detail_rows
)


two_r5_missing_resolved = all(
    row[
        "production_target_match"
    ]
    in (
        True,
        False,
    )
    for row in detail_rows
    if row[
        "r5_class"
    ]
    == "SQL_QUERY_DID_NOT_MATCH_TARGET"
)


rank_case_count = sum(
    1
    for row in detail_rows
    if row[
        "r5_class"
    ]
    == "SQL_MATCH_LOW_RANK"
)


missing_case_count = sum(
    1
    for row in detail_rows
    if row[
        "r5_class"
    ]
    == "SQL_QUERY_DID_NOT_MATCH_TARGET"
)


diagnostic_certified = all(
    (
        all_exact_population,
        rank_case_count == 7,
        missing_case_count == 2,
        all_production_truth_known,
        all_root_classified,
        two_r5_missing_resolved,
        integrity == "ok",
    )
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10-R6",

    "population": {
        "total":
            len(
                detail_rows
            ),

        "r5_rank_cases":
            rank_case_count,

        "r5_missing_cases":
            missing_case_count,
    },

    "production_match_truth": {
        "target_matches":
            production_matches,

        "target_no_matches":
            production_no_matches,

        "within_2000":
            production_within_2000,

        "beyond_2000":
            production_beyond_2000,
    },

    "r5_rank_parity": {
        "exact":
            r5_rank_parity,

        "mismatch":
            r5_rank_mismatch,
    },

    "root_class_census":
        dict(
            root_classes
        ),

    "contracts": {
        "exact_population":
            all_exact_population,

        "all_production_match_truth_known":
            all_production_truth_known,

        "all_root_classified":
            all_root_classified,

        "two_r5_missing_cases_resolved":
            two_r5_missing_resolved,

        "database_integrity":
            integrity
            == "ok",
    },

    "diagnostic_certified":
        diagnostic_certified,

    "elapsed_seconds":
        round(
            elapsed,
            3,
        ),
}


REPORT.write_text(
    json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


write_tsv(
    DETAIL,
    detail_rows,
)

write_tsv(
    VARIANTS,
    variant_rows,
)

write_tsv(
    TERMS,
    term_rows,
)

write_tsv(
    TARGET_CHUNKS,
    chunk_rows,
)


TRACE.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R6",
            " EXACT FTS MATCH TRUTH + BM25 ANATOMY",
            "=" * 78,
            "",
            *trace_lines,
        )
    ),
    encoding="utf-8",
)


SOURCE_MAP.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R6",
            " PRODUCTION FTS SOURCE CONTRACT",
            "=" * 78,
            "",
            "_fts_query",
            "-" * 78,
            inspect.getsource(
                _fts_query
            ),
            "",
            "_confidence",
            "-" * 78,
            inspect.getsource(
                _confidence
            ),
            "",
            "search_runtime_knowledge",
            "-" * 78,
            inspect.getsource(
                search_runtime_knowledge
            ),
            "",
            "DIAGNOSTIC UNLIMITED FTS QUERY",
            "-" * 78,
            """
SELECT
    f.chunk_id,
    f.document_id,
    f.title,
    f.file_path,
    bm25(runtime_chunks_fts) AS rank
FROM runtime_chunks_fts f
WHERE runtime_chunks_fts MATCH ?
ORDER BY rank
            """.strip(),
        )
    )
    + "\n",
    encoding="utf-8",
)


conn.close()


# ============================================================
# CONSOLE
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R6 RESULT")
print("=" * 78)

print()
print("POPULATION")
print("  total                       :", len(detail_rows))
print("  R5 SQL_MATCH_LOW_RANK       :", rank_case_count)
print("  R5 SQL_QUERY_NO_TARGET      :", missing_case_count)

print()
print("EXACT PRODUCTION FTS MATCH TRUTH")
print("  target matches              :", production_matches)
print("  true no-match               :", production_no_matches)
print("  rank <= 2000                :", production_within_2000)
print("  rank > 2000                 :", production_beyond_2000)

print()
print("R5 RANK PARITY")
print("  exact parity                :", r5_rank_parity)
print("  mismatch                    :", r5_rank_mismatch)

print()
print("ROOT-CAUSE CENSUS")

for key, value in sorted(
    root_classes.items(),
    key=lambda item: (
        -item[1],
        item[0],
    ),
):
    print(
        f"  {key:<52} {value}"
    )

print()
print("CERTIFICATION")

for key, value in report[
    "contracts"
].items():
    print(
        f"  {key:<42}: {value}"
    )

print()
print(
    "R4-R10-R6 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)

print()
print("Artifacts:")
print(" ", REPORT)
print(" ", DETAIL)
print(" ", VARIANTS)
print(" ", TERMS)
print(" ", TARGET_CHUNKS)
print(" ", TRACE)
print(" ", SOURCE_MAP)

print()
print(
    "elapsed seconds:",
    round(
        elapsed,
        2,
    ),
)

print("=" * 78)

raise SystemExit(
    0
    if diagnostic_certified
    else 1
)
