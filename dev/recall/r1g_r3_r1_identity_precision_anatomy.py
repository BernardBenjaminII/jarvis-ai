from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

R1G_R3_REPORT = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r3_fts_identity_shadow.json"
)

REPORT = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r3_r1_identity_precision_anatomy.json"
)

TSV = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r3_r1_identity_precision_anatomy.tsv"
)


POSITIVE_IDS = {
    19771,
    24509,
    46745,
    56981,
    69550,
    84923,
    86912,
    86958,
    89199,
}

CONTROL_IDS = {
    86876,
    86878,
    86884,
    86923,
}

ALL_IDS = POSITIVE_IDS | CONTROL_IDS


NEGATIVE_QUERIES = (
    "quantum upholstery banana zeppelin",
    "medieval sourdough GPU firmware",
    "hydraulic pastry compiler astronomy",
    "volcanic spreadsheet penguin firmware",
    "ceramic database pineapple cavalry",
    "orbital sandwich kernel theology",
    "Victorian Kubernetes broccoli engine",
    "submarine pastry JavaScript cathedral",
    "neural gearbox cinnamon telescope",
    "Apache helicopter sourdough recursion violin",
)


EXTENSIONS = {
    "pdf",
    "txt",
    "text",
    "html",
    "htm",
    "md",
    "doc",
    "docx",
    "epub",
    "rtf",
    "odt",
}


def open_ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(
        f"file:{path}?mode=ro",
        uri=True,
        timeout=30.0,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def table_exists(
    conn: sqlite3.Connection,
    table: str,
) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type IN ('table', 'view')
          AND name = ?
        LIMIT 1
        """,
        (table,),
    ).fetchone()

    return row is not None


def columns(
    conn: sqlite3.Connection,
    table: str,
) -> list[str]:
    return [
        str(row["name"])
        for row in conn.execute(
            f"PRAGMA table_info({qident(table)})"
        )
    ]


def first_existing(
    preferred: tuple[str, ...],
    available: list[str],
) -> str | None:
    amap = {
        str(name).lower(): str(name)
        for name in available
    }

    for name in preferred:
        found = amap.get(name.lower())
        if found:
            return found

    return None


def normalize_text(value: str) -> str:
    text = str(value or "")

    text = re.sub(
        r"\.(pdf|txt|text|html?|md|docx?|epub|rtf|odt)\b",
        " ",
        text,
        flags=re.I,
    )

    text = text.replace("_", " ")
    text = text.replace("/", " ")
    text = text.replace("\\", " ")

    text = re.sub(
        r"(?<=\w)[\.\(\)\[\]\{\},;:]+(?=\w)",
        " ",
        text,
    )

    text = re.sub(
        r"[\(\)\[\]\{\},;:]+",
        " ",
        text,
    )

    text = re.sub(
        r"[^\w\s'-]+",
        " ",
        text,
        flags=re.UNICODE,
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip().lower()


def tokens(value: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(
            r"[^\W_]+",
            normalize_text(value),
            flags=re.UNICODE,
        )
        if token
    ]


def meaningful_tokens(value: str) -> list[str]:
    result: list[str] = []

    for token in tokens(value):
        if token in EXTENSIONS:
            continue

        if len(token) == 1 and token.isdigit():
            continue

        result.append(token)

    return result


def quote_fts(token: str) -> str:
    return '"' + token.replace('"', '""') + '"'


def phrase_expression(query: str) -> str:
    normalized = normalize_text(query)

    if not normalized:
        return ""

    return quote_fts(normalized)


def and_expression(query: str) -> str:
    qtokens = meaningful_tokens(query)

    return " ".join(
        quote_fts(token)
        for token in qtokens
    )


def or_expression(query: str) -> str:
    qtokens = meaningful_tokens(query)

    return " OR ".join(
        quote_fts(token)
        for token in qtokens
    )


def token_overlap(
    query: str,
    text: str,
) -> dict[str, Any]:
    qtokens = meaningful_tokens(query)
    ttokens = set(
        meaningful_tokens(text)
    )

    matched = [
        token
        for token in qtokens
        if token in ttokens
    ]

    missing = [
        token
        for token in qtokens
        if token not in ttokens
    ]

    coverage = (
        len(matched) / len(qtokens)
        if qtokens
        else 0.0
    )

    return {
        "query_tokens": qtokens,
        "matched_tokens": matched,
        "missing_tokens": missing,
        "coverage": coverage,
    }


def discover_runtime_source(
    conn: sqlite3.Connection,
) -> dict[str, str]:
    table_rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """
    ).fetchall()

    tables = [
        str(row["name"])
        for row in table_rows
    ]

    preferred = [
        "runtime_documents",
        "documents",
        "knowledge_documents",
    ]

    ordered = preferred + [
        table
        for table in tables
        if table not in preferred
    ]

    for table in ordered:
        if table not in tables:
            continue

        cols = columns(conn, table)

        id_col = first_existing(
            (
                "runtime_document_id",
                "document_id",
                "id",
            ),
            cols,
        )

        title_col = first_existing(
            (
                "title",
                "document_title",
                "name",
                "filename",
            ),
            cols,
        )

        path_col = first_existing(
            (
                "file_path",
                "source_path",
                "path",
                "document_path",
            ),
            cols,
        )

        if id_col and (title_col or path_col):
            return {
                "table": table,
                "id": id_col,
                "title": title_col or "",
                "path": path_col or "",
            }

    raise RuntimeError(
        "unable to discover runtime document source"
    )


def load_runtime_rows(
    conn: sqlite3.Connection,
    source: dict[str, str],
) -> dict[int, dict[str, Any]]:
    ids = sorted(ALL_IDS)

    placeholders = ",".join(
        "?"
        for _ in ids
    )

    title_expr = (
        qident(source["title"])
        if source["title"]
        else "''"
    )

    path_expr = (
        qident(source["path"])
        if source["path"]
        else "''"
    )

    sql = f"""
        SELECT
            {qident(source['id'])} AS runtime_id,
            {title_expr} AS title,
            {path_expr} AS file_path
        FROM {qident(source['table'])}
        WHERE {qident(source['id'])}
              IN ({placeholders})
    """

    result: dict[int, dict[str, Any]] = {}

    for row in conn.execute(
        sql,
        ids,
    ):
        rid = int(row["runtime_id"])

        result[rid] = {
            "runtime_id": rid,
            "title": str(row["title"] or ""),
            "file_path": str(
                row["file_path"] or ""
            ),
        }

    return result


def load_chunk_text(
    conn: sqlite3.Connection,
    runtime_id: int,
) -> str:
    if not table_exists(
        conn,
        "runtime_chunks_fts",
    ):
        return ""

    cols = columns(
        conn,
        "runtime_chunks_fts",
    )

    if (
        "document_id" not in cols
        or "chunk_text" not in cols
    ):
        return ""

    order = (
        "CAST(chunk_id AS INTEGER)"
        if "chunk_id" in cols
        else "rowid"
    )

    rows = conn.execute(
        f"""
        SELECT chunk_text
        FROM runtime_chunks_fts
        WHERE CAST(document_id AS INTEGER) = ?
        ORDER BY {order}
        LIMIT 128
        """,
        (runtime_id,),
    ).fetchall()

    return "\n".join(
        str(row["chunk_text"] or "")
        for row in rows
    )


def create_shadow() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE VIRTUAL TABLE identity_fts
        USING fts5(
            title,
            file_path,
            runtime_id UNINDEXED,
            tokenize='unicode61'
        )
        """
    )

    conn.execute(
        """
        CREATE VIRTUAL TABLE combined_fts
        USING fts5(
            title,
            file_path,
            chunk_text,
            runtime_id UNINDEXED,
            tokenize='unicode61'
        )
        """
    )

    return conn


def insert_shadow(
    conn: sqlite3.Connection,
    row: dict[str, Any],
) -> None:
    conn.execute(
        """
        INSERT INTO identity_fts(
            title,
            file_path,
            runtime_id
        )
        VALUES (?, ?, ?)
        """,
        (
            row["title"],
            row["file_path"],
            row["runtime_id"],
        ),
    )

    conn.execute(
        """
        INSERT INTO combined_fts(
            title,
            file_path,
            chunk_text,
            runtime_id
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            row["title"],
            row["file_path"],
            row["chunk_text"],
            row["runtime_id"],
        ),
    )


def fts_search(
    conn: sqlite3.Connection,
    table: str,
    expression: str,
    *,
    limit: int = 25,
) -> list[dict[str, Any]]:
    if not expression:
        return []

    try:
        rows = conn.execute(
            f"""
            SELECT
                runtime_id,
                bm25({qident(table)}) AS score
            FROM {qident(table)}
            WHERE {qident(table)} MATCH ?
            ORDER BY bm25({qident(table)})
            LIMIT ?
            """,
            (
                expression,
                int(limit),
            ),
        ).fetchall()

    except sqlite3.Error:
        return []

    return [
        {
            "runtime_id": int(row["runtime_id"]),
            "score": float(row["score"]),
        }
        for row in rows
    ]


def rank_for(
    rows: list[dict[str, Any]],
    runtime_id: int,
) -> int | None:
    for index, row in enumerate(
        rows,
        start=1,
    ):
        if int(row["runtime_id"]) == runtime_id:
            return index

    return None


def exact_normalized_identity(
    query: str,
    title: str,
    file_path: str,
) -> bool:
    nq = normalize_text(query)

    nt = normalize_text(title)

    filename = Path(
        file_path
    ).name if file_path else ""

    nf = normalize_text(filename)

    return bool(
        nq
        and (
            nq == nt
            or nq == nf
        )
    )


def strong_identity_coverage(
    query: str,
    title: str,
    file_path: str,
) -> dict[str, Any]:
    filename = (
        Path(file_path).name
        if file_path
        else ""
    )

    identity_text = " ".join(
        (
            title,
            filename,
        )
    )

    overlap = token_overlap(
        query,
        identity_text,
    )

    qcount = len(
        overlap["query_tokens"]
    )

    coverage = float(
        overlap["coverage"]
    )

    matched = len(
        overlap["matched_tokens"]
    )

    # Diagnostic candidate rule only.
    #
    # This is deliberately not a production threshold.
    # It lets us observe whether a high-coverage identity lane
    # separates positives from the adversarial controls.
    qualifies = bool(
        qcount >= 2
        and (
            coverage >= 0.75
            or matched >= 3
        )
    )

    return {
        **overlap,
        "qualifies": qualifies,
    }


def analyze_hit(
    query: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    filename = (
        Path(row["file_path"]).name
        if row["file_path"]
        else ""
    )

    identity_text = " ".join(
        (
            row["title"],
            filename,
        )
    )

    identity = token_overlap(
        query,
        identity_text,
    )

    content = token_overlap(
        query,
        row["chunk_text"],
    )

    query_set = set(
        meaningful_tokens(query)
    )

    identity_set = set(
        identity["matched_tokens"]
    )

    content_set = set(
        content["matched_tokens"]
    )

    content_only_tokens = sorted(
        (content_set - identity_set)
        & query_set
    )

    return {
        "runtime_id": row["runtime_id"],
        "title": row["title"],
        "identity_matched_tokens": (
            identity["matched_tokens"]
        ),
        "identity_missing_tokens": (
            identity["missing_tokens"]
        ),
        "identity_coverage": (
            identity["coverage"]
        ),
        "content_matched_tokens": (
            content["matched_tokens"]
        ),
        "content_missing_tokens": (
            content["missing_tokens"]
        ),
        "content_coverage": (
            content["coverage"]
        ),
        "content_only_tokens": (
            content_only_tokens
        ),
        "content_only_match": bool(
            content["matched_tokens"]
            and not identity["matched_tokens"]
        ),
    }


def semantics_for_target(
    shadow: sqlite3.Connection,
    query: str,
    row: dict[str, Any],
) -> dict[str, Any]:
    rid = int(row["runtime_id"])

    phrase_expr = phrase_expression(
        query
    )

    and_expr = and_expression(
        query
    )

    or_expr = or_expression(
        query
    )

    phrase_rows = fts_search(
        shadow,
        "identity_fts",
        phrase_expr,
    )

    and_rows = fts_search(
        shadow,
        "identity_fts",
        and_expr,
    )

    or_rows = fts_search(
        shadow,
        "identity_fts",
        or_expr,
    )

    combined_rows = fts_search(
        shadow,
        "combined_fts",
        or_expr,
    )

    strong = strong_identity_coverage(
        query,
        row["title"],
        row["file_path"],
    )

    return {
        "A_exact_normalized_identity": (
            exact_normalized_identity(
                query,
                row["title"],
                row["file_path"],
            )
        ),
        "A_phrase_rank": rank_for(
            phrase_rows,
            rid,
        ),
        "B_identity_and_rank": rank_for(
            and_rows,
            rid,
        ),
        "C_strong_identity_coverage": (
            strong
        ),
        "D_identity_or_rank": rank_for(
            or_rows,
            rid,
        ),
        "E_combined_or_rank": rank_for(
            combined_rows,
            rid,
        ),
        "expressions": {
            "phrase": phrase_expr,
            "and": and_expr,
            "or": or_expr,
        },
    }


def analyze_negative(
    shadow: sqlite3.Connection,
    query: str,
    rows_by_id: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    phrase_expr = phrase_expression(
        query
    )

    and_expr = and_expression(
        query
    )

    or_expr = or_expression(
        query
    )

    phrase_rows = fts_search(
        shadow,
        "identity_fts",
        phrase_expr,
    )

    and_rows = fts_search(
        shadow,
        "identity_fts",
        and_expr,
    )

    identity_or_rows = fts_search(
        shadow,
        "identity_fts",
        or_expr,
    )

    combined_or_rows = fts_search(
        shadow,
        "combined_fts",
        or_expr,
    )

    identity_hits: list[dict[str, Any]] = []

    for hit in identity_or_rows:
        rid = int(hit["runtime_id"])

        row = rows_by_id.get(rid)

        if row is None:
            continue

        anatomy = analyze_hit(
            query,
            row,
        )

        anatomy["rank"] = (
            rank_for(
                identity_or_rows,
                rid,
            )
        )

        anatomy["score"] = hit["score"]

        identity_hits.append(
            anatomy
        )

    combined_hits: list[dict[str, Any]] = []

    for hit in combined_or_rows:
        rid = int(hit["runtime_id"])

        row = rows_by_id.get(rid)

        if row is None:
            continue

        anatomy = analyze_hit(
            query,
            row,
        )

        anatomy["rank"] = (
            rank_for(
                combined_or_rows,
                rid,
            )
        )

        anatomy["score"] = hit["score"]

        combined_hits.append(
            anatomy
        )

    strong_candidates = []

    for rid, row in sorted(
        rows_by_id.items()
    ):
        strong = strong_identity_coverage(
            query,
            row["title"],
            row["file_path"],
        )

        if strong["qualifies"]:
            strong_candidates.append(
                {
                    "runtime_id": rid,
                    "title": row["title"],
                    **strong,
                }
            )

    return {
        "query": query,
        "query_tokens": meaningful_tokens(
            query
        ),
        "A_phrase_hits": len(
            phrase_rows
        ),
        "B_identity_and_hits": len(
            and_rows
        ),
        "C_strong_identity_hits": len(
            strong_candidates
        ),
        "D_identity_or_hits": len(
            identity_or_rows
        ),
        "E_combined_or_hits": len(
            combined_or_rows
        ),
        "strong_candidates": (
            strong_candidates
        ),
        "identity_or_matches": (
            identity_hits
        ),
        "combined_or_matches": (
            combined_hits
        ),
    }


def main() -> int:
    started = time.monotonic()

    print("=" * 72)
    print(" GENESIS RECALL R1G-R3-R1")
    print(" IDENTITY PRECISION + MATCH-SEMANTICS ANATOMY")
    print("=" * 72)

    data = json.loads(
        R1G_R3_REPORT.read_text(
            encoding="utf-8"
        )
    )

    previous_results = data.get(
        "hard_failure_results",
        [],
    )

    previous_controls = data.get(
        "controls",
        [],
    )

    query_by_id: dict[int, str] = {}

    for item in (
        previous_results
        + previous_controls
    ):
        rid = int(
            item["runtime_id"]
        )

        query_by_id[rid] = str(
            item.get("query")
            or item.get("title")
            or ""
        )

    missing_queries = (
        ALL_IDS
        - set(query_by_id)
    )

    if missing_queries:
        print(
            "FAIL: R1G-R3 report missing queries:",
            sorted(missing_queries),
        )
        return 2

    production = open_ro(DB)

    source = discover_runtime_source(
        production
    )

    print()
    print("=== RUNTIME SOURCE ===")
    print("table :", source["table"])
    print("id    :", source["id"])
    print("title :", source["title"] or None)
    print("path  :", source["path"] or None)

    rows_by_id = load_runtime_rows(
        production,
        source,
    )

    missing_rows = (
        ALL_IDS
        - set(rows_by_id)
    )

    if missing_rows:
        print(
            "FAIL: runtime rows missing:",
            sorted(missing_rows),
        )
        production.close()
        return 2

    for rid, row in rows_by_id.items():
        row["chunk_text"] = load_chunk_text(
            production,
            rid,
        )

    shadow = create_shadow()

    for row in rows_by_id.values():
        insert_shadow(
            shadow,
            row,
        )

    shadow.commit()

    print()
    print("=" * 72)
    print(" POSITIVE MATCH-SEMANTICS MATRIX")
    print("=" * 72)

    positive_results: list[
        dict[str, Any]
    ] = []

    for index, rid in enumerate(
        sorted(POSITIVE_IDS),
        start=1,
    ):
        row = rows_by_id[rid]

        query = query_by_id[rid]

        semantics = semantics_for_target(
            shadow,
            query,
            row,
        )

        result = {
            "runtime_id": rid,
            "title": row["title"],
            "query": query,
            **semantics,
        }

        positive_results.append(
            result
        )

        print()
        print(
            f"[{index:02d}/09] id={rid}"
        )
        print(
            "title              :",
            row["title"],
        )
        print(
            "query              :",
            query,
        )
        print(
            "A exact identity   :",
            semantics[
                "A_exact_normalized_identity"
            ],
        )
        print(
            "A phrase rank      :",
            semantics[
                "A_phrase_rank"
            ],
        )
        print(
            "B identity AND     :",
            semantics[
                "B_identity_and_rank"
            ],
        )
        print(
            "C strong coverage  :",
            semantics[
                "C_strong_identity_coverage"
            ]["qualifies"],
            f"coverage="
            f"{semantics['C_strong_identity_coverage']['coverage']:.3f}",
        )
        print(
            "D identity OR      :",
            semantics[
                "D_identity_or_rank"
            ],
        )
        print(
            "E combined OR      :",
            semantics[
                "E_combined_or_rank"
            ],
        )

    print()
    print("=" * 72)
    print(" CONTROL MATCH-SEMANTICS MATRIX")
    print("=" * 72)

    control_results: list[
        dict[str, Any]
    ] = []

    for rid in sorted(
        CONTROL_IDS
    ):
        row = rows_by_id[rid]

        query = query_by_id[rid]

        semantics = semantics_for_target(
            shadow,
            query,
            row,
        )

        result = {
            "runtime_id": rid,
            "title": row["title"],
            "query": query,
            **semantics,
        }

        control_results.append(
            result
        )

        print()
        print("id                 :", rid)
        print("title              :", row["title"])
        print(
            "A exact identity   :",
            semantics[
                "A_exact_normalized_identity"
            ],
        )
        print(
            "A phrase rank      :",
            semantics[
                "A_phrase_rank"
            ],
        )
        print(
            "B identity AND     :",
            semantics[
                "B_identity_and_rank"
            ],
        )
        print(
            "C strong coverage  :",
            semantics[
                "C_strong_identity_coverage"
            ]["qualifies"],
        )
        print(
            "D identity OR      :",
            semantics[
                "D_identity_or_rank"
            ],
        )
        print(
            "E combined OR      :",
            semantics[
                "E_combined_or_rank"
            ],
        )

    print()
    print("=" * 72)
    print(" ADVERSARIAL MATCH ANATOMY")
    print("=" * 72)

    negative_results: list[
        dict[str, Any]
    ] = []

    for query in NEGATIVE_QUERIES:
        result = analyze_negative(
            shadow,
            query,
            rows_by_id,
        )

        negative_results.append(
            result
        )

        print()
        print("-" * 72)
        print("query :", query)
        print("-" * 72)
        print(
            "A phrase hits          :",
            result["A_phrase_hits"],
        )
        print(
            "B identity AND hits    :",
            result[
                "B_identity_and_hits"
            ],
        )
        print(
            "C strong identity hits :",
            result[
                "C_strong_identity_hits"
            ],
        )
        print(
            "D identity OR hits     :",
            result[
                "D_identity_or_hits"
            ],
        )
        print(
            "E combined OR hits     :",
            result[
                "E_combined_or_hits"
            ],
        )

        if result[
            "identity_or_matches"
        ]:
            print()
            print("IDENTITY OR MATCHES")

            for hit in result[
                "identity_or_matches"
            ]:
                print(
                    "  id=",
                    hit["runtime_id"],
                    " rank=",
                    hit["rank"],
                    " title=",
                    hit["title"],
                    sep="",
                )
                print(
                    "    identity tokens :",
                    hit[
                        "identity_matched_tokens"
                    ],
                )
                print(
                    "    identity coverage:",
                    f"{hit['identity_coverage']:.3f}",
                )

        if result[
            "combined_or_matches"
        ]:
            print()
            print("COMBINED OR MATCHES")

            for hit in result[
                "combined_or_matches"
            ]:
                print(
                    "  id=",
                    hit["runtime_id"],
                    " rank=",
                    hit["rank"],
                    " title=",
                    hit["title"],
                    sep="",
                )
                print(
                    "    identity tokens :",
                    hit[
                        "identity_matched_tokens"
                    ],
                )
                print(
                    "    content tokens  :",
                    hit[
                        "content_matched_tokens"
                    ],
                )
                print(
                    "    content-only    :",
                    hit[
                        "content_only_tokens"
                    ],
                )
                print(
                    "    identity cov    :",
                    f"{hit['identity_coverage']:.3f}",
                )
                print(
                    "    content cov     :",
                    f"{hit['content_coverage']:.3f}",
                )

    def positive_count(
        predicate,
    ) -> int:
        return sum(
            1
            for item in positive_results
            if predicate(item)
        )

    def control_count(
        predicate,
    ) -> int:
        return sum(
            1
            for item in control_results
            if predicate(item)
        )

    positive_A = positive_count(
        lambda item:
        item[
            "A_exact_normalized_identity"
        ]
        or item["A_phrase_rank"]
        is not None
    )

    positive_B = positive_count(
        lambda item:
        item["B_identity_and_rank"]
        is not None
    )

    positive_C = positive_count(
        lambda item:
        bool(
            item[
                "C_strong_identity_coverage"
            ]["qualifies"]
        )
    )

    positive_D = positive_count(
        lambda item:
        item["D_identity_or_rank"]
        is not None
    )

    positive_E = positive_count(
        lambda item:
        item["E_combined_or_rank"]
        is not None
    )

    control_A = control_count(
        lambda item:
        item[
            "A_exact_normalized_identity"
        ]
        or item["A_phrase_rank"]
        is not None
    )

    control_B = control_count(
        lambda item:
        item["B_identity_and_rank"]
        is not None
    )

    control_C = control_count(
        lambda item:
        bool(
            item[
                "C_strong_identity_coverage"
            ]["qualifies"]
        )
    )

    control_D = control_count(
        lambda item:
        item["D_identity_or_rank"]
        is not None
    )

    control_E = control_count(
        lambda item:
        item["E_combined_or_rank"]
        is not None
    )

    negative_A = sum(
        1
        for item in negative_results
        if item["A_phrase_hits"] > 0
    )

    negative_B = sum(
        1
        for item in negative_results
        if item[
            "B_identity_and_hits"
        ] > 0
    )

    negative_C = sum(
        1
        for item in negative_results
        if item[
            "C_strong_identity_hits"
        ] > 0
    )

    negative_D = sum(
        1
        for item in negative_results
        if item[
            "D_identity_or_hits"
        ] > 0
    )

    negative_E = sum(
        1
        for item in negative_results
        if item[
            "E_combined_or_hits"
        ] > 0
    )

    # This pack certifies the ANATOMY, not a production policy.
    #
    # We require:
    #   * all known positive cases were evaluated,
    #   * all controls were evaluated,
    #   * all adversarial cases were evaluated,
    #   * strict AND semantics produce no adversarial hit,
    #   * strong identity coverage produces no adversarial hit.
    #
    # We intentionally do NOT require any arbitrary positive
    # recovery percentage.
    anatomy_certified = (
        len(positive_results) == 9
        and len(control_results) == 4
        and len(negative_results) == 10
        and negative_B == 0
        and negative_C == 0
    )

    elapsed = (
        time.monotonic()
        - started
    )

    summary = {
        "pack": (
            "Genesis Recall R1G-R3-R1"
        ),
        "purpose": (
            "Identity precision and "
            "match-semantics anatomy"
        ),
        "production_source_changes": 0,
        "production_db_writes": 0,
        "shadow_database": ":memory:",
        "runtime_source": source,
        "positive_cases": len(
            positive_results
        ),
        "control_cases": len(
            control_results
        ),
        "negative_cases": len(
            negative_results
        ),
        "positive_recovery": {
            "A_exact_or_phrase": positive_A,
            "B_identity_and": positive_B,
            "C_strong_identity_coverage": positive_C,
            "D_identity_or": positive_D,
            "E_combined_or": positive_E,
        },
        "control_recovery": {
            "A_exact_or_phrase": control_A,
            "B_identity_and": control_B,
            "C_strong_identity_coverage": control_C,
            "D_identity_or": control_D,
            "E_combined_or": control_E,
        },
        "negative_query_hits": {
            "A_exact_phrase": negative_A,
            "B_identity_and": negative_B,
            "C_strong_identity_coverage": negative_C,
            "D_identity_or": negative_D,
            "E_combined_or": negative_E,
        },
        "anatomy_certified": (
            anatomy_certified
        ),
        "elapsed_seconds": elapsed,
        "positive_results": (
            positive_results
        ),
        "control_results": (
            control_results
        ),
        "negative_results": (
            negative_results
        ),
    }

    REPORT.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    with TSV.open(
        "w",
        encoding="utf-8",
    ) as fh:
        fh.write(
            "\t".join(
                (
                    "class",
                    "runtime_id",
                    "title",
                    "query",
                    "A_exact",
                    "A_phrase_rank",
                    "B_and_rank",
                    "C_strong",
                    "C_coverage",
                    "D_or_rank",
                    "E_combined_rank",
                )
            )
            + "\n"
        )

        for class_name, collection in (
            (
                "positive",
                positive_results,
            ),
            (
                "control",
                control_results,
            ),
        ):
            for item in collection:
                strong = item[
                    "C_strong_identity_coverage"
                ]

                fh.write(
                    "\t".join(
                        (
                            class_name,
                            str(
                                item[
                                    "runtime_id"
                                ]
                            ),
                            item["title"].replace(
                                "\t",
                                " ",
                            ),
                            item["query"].replace(
                                "\t",
                                " ",
                            ),
                            str(
                                item[
                                    "A_exact_normalized_identity"
                                ]
                            ),
                            str(
                                item[
                                    "A_phrase_rank"
                                ]
                                or ""
                            ),
                            str(
                                item[
                                    "B_identity_and_rank"
                                ]
                                or ""
                            ),
                            str(
                                strong[
                                    "qualifies"
                                ]
                            ),
                            (
                                f"{strong['coverage']:.6f}"
                            ),
                            str(
                                item[
                                    "D_identity_or_rank"
                                ]
                                or ""
                            ),
                            str(
                                item[
                                    "E_combined_or_rank"
                                ]
                                or ""
                            ),
                        )
                    )
                    + "\n"
                )

    print()
    print("=" * 72)
    print(" R1G-R3-R1 MATCH-SEMANTICS SUMMARY")
    print("=" * 72)

    print()
    print("KNOWN HARD FAILURES")
    print(
        "  A exact/phrase       :",
        f"{positive_A}/9",
    )
    print(
        "  B identity AND       :",
        f"{positive_B}/9",
    )
    print(
        "  C strong coverage    :",
        f"{positive_C}/9",
    )
    print(
        "  D identity OR        :",
        f"{positive_D}/9",
    )
    print(
        "  E combined OR        :",
        f"{positive_E}/9",
    )

    print()
    print("RECOVERABLE CONTROLS")
    print(
        "  A exact/phrase       :",
        f"{control_A}/4",
    )
    print(
        "  B identity AND       :",
        f"{control_B}/4",
    )
    print(
        "  C strong coverage    :",
        f"{control_C}/4",
    )
    print(
        "  D identity OR        :",
        f"{control_D}/4",
    )
    print(
        "  E combined OR        :",
        f"{control_E}/4",
    )

    print()
    print("ADVERSARIAL QUERIES WITH >=1 HIT")
    print(
        "  A exact phrase       :",
        f"{negative_A}/10",
    )
    print(
        "  B identity AND       :",
        f"{negative_B}/10",
    )
    print(
        "  C strong coverage    :",
        f"{negative_C}/10",
    )
    print(
        "  D identity OR        :",
        f"{negative_D}/10",
    )
    print(
        "  E combined OR        :",
        f"{negative_E}/10",
    )

    print()
    print(
        "ANATOMY CERTIFIED      :",
        anatomy_certified,
    )
    print(
        "elapsed seconds        :",
        f"{elapsed:.2f}",
    )
    print("=" * 72)

    shadow.close()
    production.close()

    return (
        0
        if anatomy_certified
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
