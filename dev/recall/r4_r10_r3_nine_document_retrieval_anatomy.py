from __future__ import annotations

import csv
import inspect
import json
import re
import sqlite3
import sys
import time

from collections import Counter
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

UNRESOLVED_IN = (
    OUTDIR
    / "r4_r10_r2_unresolved_targets.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r3_nine_document_retrieval_anatomy.json"
)

DETAIL = (
    OUTDIR
    / "r4_r10_r3_nine_document_retrieval_anatomy.tsv"
)

CHUNKS = (
    OUTDIR
    / "r4_r10_r3_chunk_population.tsv"
)

FTS = (
    OUTDIR
    / "r4_r10_r3_fts_presence.tsv"
)

SEARCH_TRACE = (
    OUTDIR
    / "r4_r10_r3_search_exposure.tsv"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r3_search_source_map.txt"
)

TRACE = (
    OUTDIR
    / "r4_r10_r3_retrieval_trace.txt"
)


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.search import (
    search_catalog,
)


EXPECTED = 9


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


def text(value: Any) -> str:

    if value is None:
        return ""

    return str(value).strip()


def ident_equal(
    left: Any,
    right: Any,
) -> bool:

    a = text(left)
    b = text(right)

    if not a or not b:
        return False

    if a.casefold() == b.casefold():
        return True

    try:
        return int(a) == int(b)
    except Exception:
        return False


def row_map(raw: Any) -> dict[str, Any]:

    if isinstance(raw, Mapping):
        return dict(raw)

    if hasattr(raw, "keys"):
        try:
            return {
                key: raw[key]
                for key in raw.keys()
            }
        except Exception:
            pass

    if hasattr(raw, "_asdict"):
        try:
            return dict(raw._asdict())
        except Exception:
            pass

    try:
        return dict(vars(raw))
    except Exception:
        return {}


def first_present(
    row: Mapping[str, Any],
    *names: str,
) -> str:

    lowered = {
        str(k).casefold(): k
        for k in row.keys()
    }

    for name in names:
        key = lowered.get(
            name.casefold()
        )

        if key is None:
            continue

        value = row.get(key)

        if value not in (
            None,
            "",
        ):
            return text(value)

    return ""


# ============================================================
# READ-ONLY SQLITE
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
        f"DB integrity failure: {integrity}"
    )


# ============================================================
# SCHEMA DISCOVERY
# ============================================================

tables = [
    row["name"]
    for row in conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    )
]


table_cols: dict[str, list[str]] = {}

fts_tables = []

for table in tables:

    cols = [
        row["name"]
        for row in conn.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()
    ]

    table_cols[table] = cols

    sql = conn.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        """,
        (table,),
    ).fetchone()

    create_sql = (
        sql["sql"]
        if sql
        else ""
    ) or ""

    if "fts" in create_sql.casefold():
        fts_tables.append(table)


# ============================================================
# TABLE ROLE DISCOVERY
# ============================================================

document_tables = []

chunk_tables = []

for table, cols in table_cols.items():

    lowered = {
        c.casefold()
        for c in cols
    }

    if (
        "document_id" in lowered
        or
        (
            "id" in lowered
            and
            (
                "title" in lowered
                or "subject" in lowered
                or "source_path" in lowered
                or "path" in lowered
            )
        )
    ):
        document_tables.append(table)

    if (
        "chunk_id" in lowered
        or
        (
            "document_id" in lowered
            and
            any(
                name in lowered
                for name in (
                    "text",
                    "content",
                    "excerpt",
                    "chunk_text",
                    "body",
                )
            )
        )
    ):
        chunk_tables.append(table)


# ============================================================
# DB DOCUMENT LOOKUP
# ============================================================

def db_document_hits(
    target_id: str,
) -> list[dict[str, Any]]:

    hits = []

    for table in document_tables:

        cols = table_cols[table]

        id_candidates = [
            c
            for c in cols
            if c.casefold() in {
                "document_id",
                "id",
                "runtime_document_id",
            }
        ]

        for col in id_candidates:

            try:
                rows = conn.execute(
                    f'''
                    SELECT rowid AS "__rowid__", *
                    FROM "{table}"
                    WHERE CAST("{col}" AS TEXT) = ?
                    LIMIT 25
                    ''',
                    (target_id,),
                ).fetchall()
            except sqlite3.DatabaseError:
                continue

            for row in rows:

                mapped = dict(row)

                hits.append(
                    {
                        "table": table,
                        "id_column": col,
                        "row": mapped,
                    }
                )

    return hits


# ============================================================
# CHUNK LOOKUP
# ============================================================

def chunk_hits(
    target_id: str,
) -> list[dict[str, Any]]:

    results = []

    for table in chunk_tables:

        cols = table_cols[table]

        doc_cols = [
            c
            for c in cols
            if c.casefold() in {
                "document_id",
                "runtime_document_id",
                "doc_id",
                "parent_document_id",
            }
        ]

        for col in doc_cols:

            try:
                rows = conn.execute(
                    f'''
                    SELECT rowid AS "__rowid__", *
                    FROM "{table}"
                    WHERE CAST("{col}" AS TEXT) = ?
                    LIMIT 5000
                    ''',
                    (target_id,),
                ).fetchall()
            except sqlite3.DatabaseError:
                continue

            for row in rows:

                mapped = dict(row)

                results.append(
                    {
                        "table": table,
                        "document_column": col,
                        "row": mapped,
                    }
                )

    return results


# ============================================================
# FTS ROW MATCHING BY CHUNK/DOCUMENT ID
# ============================================================

def fts_identity_presence(
    target_id: str,
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    results = []

    chunk_ids = set()

    for item in chunks:

        row = item["row"]

        for key in (
            "chunk_id",
            "id",
            "source_id",
        ):
            value = row.get(key)

            if value not in (
                None,
                "",
            ):
                chunk_ids.add(
                    text(value)
                )

    for table in fts_tables:

        cols = table_cols[table]

        candidate_id_cols = [
            c
            for c in cols
            if c.casefold() in {
                "document_id",
                "chunk_id",
                "id",
                "source_id",
            }
        ]

        for col in candidate_id_cols:

            targets = {
                target_id,
                *chunk_ids,
            }

            for value in targets:

                try:
                    rows = conn.execute(
                        f'''
                        SELECT rowid AS "__rowid__", *
                        FROM "{table}"
                        WHERE CAST("{col}" AS TEXT) = ?
                        LIMIT 100
                        ''',
                        (value,),
                    ).fetchall()
                except sqlite3.DatabaseError:
                    continue

                for row in rows:

                    mapped = dict(row)

                    results.append(
                        {
                            "table": table,
                            "id_column": col,
                            "matched_value": value,
                            "row": mapped,
                        }
                    )

    return results


# ============================================================
# FTS QUERY MATCH
# ============================================================

def safe_fts_query_terms(
    query: str,
) -> list[str]:

    return [
        token.casefold()
        for token in re.findall(
            r"[A-Za-z0-9]+",
            query,
        )
        if len(token) >= 2
    ]


def direct_fts_matches(
    query: str,
    target_id: str,
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    results = []

    terms = safe_fts_query_terms(
        query
    )

    if not terms:
        return results

    match_expr = " OR ".join(
        f'"{term}"'
        for term in terms
    )

    chunk_ids = set()

    for item in chunks:

        row = item["row"]

        for key in (
            "chunk_id",
            "id",
            "source_id",
        ):
            value = row.get(key)

            if value not in (
                None,
                "",
            ):
                chunk_ids.add(
                    text(value)
                )

    for table in fts_tables:

        try:
            rows = conn.execute(
                f'''
                SELECT rowid AS "__rowid__", *
                FROM "{table}"
                WHERE "{table}" MATCH ?
                LIMIT 1000
                ''',
                (match_expr,),
            ).fetchall()
        except sqlite3.DatabaseError:
            continue

        rank = 0

        for row in rows:

            rank += 1

            mapped = dict(row)

            identities = {
                text(mapped.get(k))
                for k in (
                    "document_id",
                    "chunk_id",
                    "id",
                    "source_id",
                )
                if mapped.get(k) not in (
                    None,
                    "",
                )
            }

            target_hit = (
                any(
                    ident_equal(
                        target_id,
                        value,
                    )
                    for value in identities
                )
                or
                any(
                    value in chunk_ids
                    for value in identities
                )
            )

            if target_hit:

                results.append(
                    {
                        "table": table,
                        "match_expression": match_expr,
                        "rank": rank,
                        "row": mapped,
                    }
                )

    return results


# ============================================================
# PRODUCTION SEARCH EXPOSURE
# ============================================================

def production_exposure(
    query: str,
    target_id: str,
) -> dict[str, Any]:

    limits = (
        20,
        50,
        100,
        250,
        500,
        1000,
        2000,
    )

    attempts = []

    for limit in limits:

        rows = list(
            search_catalog(
                query,
                limit=limit,
            )
        )

        target_rank = None
        target_chunk_ids = []

        for rank, raw in enumerate(
            rows,
            start=1,
        ):

            mapped = row_map(raw)

            document_id = first_present(
                mapped,
                "document_id",
                "runtime_document_id",
                "doc_id",
            )

            if ident_equal(
                document_id,
                target_id,
            ):
                target_rank = rank

                for key in (
                    "chunk_id",
                    "source_id",
                    "id",
                ):
                    value = mapped.get(key)

                    if value not in (
                        None,
                        "",
                    ):
                        target_chunk_ids.append(
                            text(value)
                        )

                break

        attempts.append(
            {
                "limit": limit,
                "returned": len(rows),
                "target_rank": target_rank,
            }
        )

        if target_rank is not None:

            return {
                "found": True,
                "rank": target_rank,
                "limit": limit,
                "attempts": attempts,
                "chunk_ids": target_chunk_ids,
            }

    return {
        "found": False,
        "rank": None,
        "limit": limits[-1],
        "attempts": attempts,
        "chunk_ids": [],
    }


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(
    *,
    document_hits: int,
    chunk_count: int,
    fts_identity_count: int,
    fts_match_count: int,
    production_found: bool,
) -> str:

    if document_hits == 0:
        return "DOCUMENT_ROW_MISSING"

    if chunk_count == 0:
        return "DOCUMENT_HAS_NO_CHUNKS"

    if fts_identity_count == 0:
        return "CHUNKS_NOT_IN_FTS"

    if fts_match_count == 0:
        return "FTS_PRESENT_BUT_QUERY_NO_MATCH"

    if fts_match_count > 0 and not production_found:
        return "FTS_MATCH_FILTERED_BEFORE_RESULT_MATERIALIZATION"

    if production_found:
        return "PRODUCTION_SEARCH_EXPOSED_TARGET"

    return "OTHER"


# ============================================================
# RUN NINE-DOCUMENT TRACE
# ============================================================

unresolved = read_tsv(
    UNRESOLVED_IN
)

if len(unresolved) != EXPECTED:
    raise RuntimeError(
        f"expected 9 unresolved targets, got {len(unresolved)}"
    )


started = time.time()

detail_rows = []
chunk_rows = []
fts_rows = []
search_rows = []
trace_lines = []

class_counter = Counter()

all_document_rows_present = True
all_chunk_state_known = True
all_fts_state_known = True


for index, item in enumerate(
    unresolved,
    start=1,
):

    target_id = item["target_id"]
    query = item["query"]

    docs = db_document_hits(
        target_id
    )

    chunks = chunk_hits(
        target_id
    )

    fts_identity = fts_identity_presence(
        target_id,
        chunks,
    )

    fts_direct = direct_fts_matches(
        query,
        target_id,
        chunks,
    )

    prod = production_exposure(
        query,
        target_id,
    )

    diagnosis = classify(
        document_hits=len(docs),
        chunk_count=len(chunks),
        fts_identity_count=len(fts_identity),
        fts_match_count=len(fts_direct),
        production_found=bool(
            prod["found"]
        ),
    )

    class_counter[
        diagnosis
    ] += 1


    if not docs:
        all_document_rows_present = False


    # Document metadata preview
    doc_title = ""
    doc_subject = ""
    doc_path = ""

    if docs:
        row = docs[0]["row"]

        doc_title = first_present(
            row,
            "title",
            "name",
            "document_title",
        )

        doc_subject = first_present(
            row,
            "subject",
            "document_subject",
        )

        doc_path = first_present(
            row,
            "source_path",
            "path",
            "file_path",
            "filepath",
        )


    # Chunk rows
    for chunk in chunks:

        row = chunk["row"]

        chunk_rows.append(
            {
                "case": index,
                "document_id": target_id,
                "query": query,
                "table": chunk["table"],
                "document_column":
                    chunk["document_column"],
                "chunk_id":
                    first_present(
                        row,
                        "chunk_id",
                        "id",
                        "source_id",
                    ),
                "text_preview":
                    first_present(
                        row,
                        "text",
                        "content",
                        "excerpt",
                        "chunk_text",
                        "body",
                    )[:300],
            }
        )


    # FTS rows
    for hit in fts_identity:

        row = hit["row"]

        fts_rows.append(
            {
                "case": index,
                "document_id": target_id,
                "query": query,
                "mode": "IDENTITY_PRESENCE",
                "table": hit["table"],
                "id_column": hit["id_column"],
                "matched_value":
                    hit["matched_value"],
                "rank": "",
                "row_preview":
                    json.dumps(
                        {
                            k: row[k]
                            for k in list(
                                row.keys()
                            )[:10]
                        },
                        ensure_ascii=False,
                        default=str,
                    )[:1000],
            }
        )


    for hit in fts_direct:

        row = hit["row"]

        fts_rows.append(
            {
                "case": index,
                "document_id": target_id,
                "query": query,
                "mode": "DIRECT_QUERY_MATCH",
                "table": hit["table"],
                "id_column": "",
                "matched_value": "",
                "rank": hit["rank"],
                "row_preview":
                    json.dumps(
                        {
                            k: row[k]
                            for k in list(
                                row.keys()
                            )[:10]
                        },
                        ensure_ascii=False,
                        default=str,
                    )[:1000],
            }
        )


    for attempt in prod["attempts"]:

        search_rows.append(
            {
                "case": index,
                "document_id": target_id,
                "query": query,
                "limit": attempt["limit"],
                "returned": attempt["returned"],
                "target_rank":
                    attempt["target_rank"],
            }
        )


    detail_rows.append(
        {
            "case": index,
            "document_id": target_id,
            "query": query,

            "document_rows":
                len(docs),

            "document_title":
                doc_title,

            "document_subject":
                doc_subject,

            "document_path":
                doc_path,

            "chunk_count":
                len(chunks),

            "fts_identity_rows":
                len(fts_identity),

            "fts_query_matches":
                len(fts_direct),

            "production_found":
                bool(
                    prod["found"]
                ),

            "production_rank":
                prod["rank"],

            "production_limit":
                prod["limit"],

            "diagnosis":
                diagnosis,
        }
    )


    trace_lines.extend(
        [
            "=" * 78,
            f"CASE {index:02d}",
            "=" * 78,
            f"document_id       : {target_id}",
            f"query             : {query}",
            f"title             : {doc_title}",
            f"subject           : {doc_subject}",
            f"path              : {doc_path}",
            "",
            f"document rows     : {len(docs)}",
            f"chunk count       : {len(chunks)}",
            f"FTS identity rows : {len(fts_identity)}",
            f"FTS query matches : {len(fts_direct)}",
            f"production found  : {prod['found']}",
            f"production rank   : {prod['rank']}",
            f"max search limit  : {prod['limit']}",
            "",
            f"DIAGNOSIS         : {diagnosis}",
            "",
        ]
    )


# ============================================================
# WRITE ARTIFACTS
# ============================================================

write_tsv(
    DETAIL,
    detail_rows,
)

write_tsv(
    CHUNKS,
    chunk_rows,
)

write_tsv(
    FTS,
    fts_rows,
)

write_tsv(
    SEARCH_TRACE,
    search_rows,
)


TRACE.write_text(
    "\n".join(
        [
            "=" * 78,
            " GENESIS RECALL R4-R10-R3",
            " NINE-DOCUMENT RAW RETRIEVAL TRACE",
            "=" * 78,
            "",
            *trace_lines,
        ]
    ),
    encoding="utf-8",
)


# ============================================================
# SOURCE MAP
# ============================================================

source_parts = [
    "=" * 78,
    "PRODUCTION search_catalog",
    "=" * 78,
]

try:
    source_parts.append(
        inspect.getsource(
            search_catalog
        )
    )
except Exception as exc:
    source_parts.append(
        f"SOURCE ERROR: {type(exc).__name__}: {exc}"
    )


SOURCE_MAP.write_text(
    "\n".join(
        source_parts
    ),
    encoding="utf-8",
)


# ============================================================
# CERTIFICATION
# ============================================================

all_classified = (
    len(detail_rows) == EXPECTED
    and
    sum(
        class_counter.values()
    ) == EXPECTED
)


no_unknown = (
    class_counter.get(
        "OTHER",
        0,
    )
    == 0
)


diagnostic_certified = (
    len(unresolved) == EXPECTED
    and
    all_classified
    and
    all_document_rows_present
    and
    all_chunk_state_known
    and
    all_fts_state_known
    and
    no_unknown
    and
    integrity == "ok"
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10-R3",

    "population": {
        "expected":
            EXPECTED,

        "actual":
            len(unresolved),

        "classified":
            len(detail_rows),
    },

    "diagnosis_census":
        dict(
            class_counter
        ),

    "contracts": {
        "all_document_rows_present":
            all_document_rows_present,

        "all_chunk_state_known":
            all_chunk_state_known,

        "all_fts_state_known":
            all_fts_state_known,

        "no_unknown_class":
            no_unknown,

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


conn.close()


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R3 RESULT")
print("=" * 78)

print()
print("POPULATION")

print(
    "  expected                    :",
    EXPECTED,
)

print(
    "  actual                      :",
    len(unresolved),
)

print(
    "  classified                  :",
    len(detail_rows),
)


print()
print("DIAGNOSIS CENSUS")

for key, value in sorted(
    class_counter.items(),
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

print(
    "  all document rows present   :",
    all_document_rows_present,
)

print(
    "  all chunk state known        :",
    all_chunk_state_known,
)

print(
    "  all FTS state known          :",
    all_fts_state_known,
)

print(
    "  no unknown class             :",
    no_unknown,
)

print(
    "  DB integrity                 :",
    integrity,
)


print()
print(
    "R4-R10-R3 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)


print()
print("Artifacts:")
print(" ", REPORT)
print(" ", DETAIL)
print(" ", CHUNKS)
print(" ", FTS)
print(" ", SEARCH_TRACE)
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
