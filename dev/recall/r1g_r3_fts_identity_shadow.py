from __future__ import annotations

import json
import re
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

R1G_R2_REPORT = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r2_fts_candidate_anatomy.json"
)

REPORT = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r3_fts_identity_shadow.json"
)

TSV = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r3_fts_identity_shadow.tsv"
)

TOKEN_REPORT = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r1g_r3_tokenization.txt"
)


EXPECTED_FAILURE_IDS = {
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

EXPECTED_RECOVERABLE_IDS = {
    86876,
    86878,
    86884,
    86923,
}


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


TOKEN_PROBES = (
    "Riyadh us Saliheem.pdf",
    "RIYAD US–SALIHEEN",
    "la ta7zan.pdf",
    "Guevara, Che - Guerilla Warfare.pdf",
    "List (Sora names).txt",
    "2.1 pyper.txt.txt",
    "3.1 macchanger.txt.txt",
    "Edward.William.Lane's.Arabic-English.Lexicon.(Dictionary).-.Vol.6.pdf",
    "kameez pattern.pdf",
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
    uri = f"file:{path}?mode=ro"
    conn = sqlite3.connect(
        uri,
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
    names: Iterable[str],
    available: Iterable[str],
) -> str | None:
    amap = {
        str(name).lower(): str(name)
        for name in available
    }
    for name in names:
        found = amap.get(name.lower())
        if found:
            return found
    return None


def normalize_query(value: str) -> str:
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

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def query_tokens(value: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(
            r"[^\W_]+",
            normalize_query(value),
            flags=re.UNICODE,
        )
        if token
    ]


def relaxed_tokens(value: str) -> list[str]:
    raw = query_tokens(value)

    result: list[str] = []

    for token in raw:
        if token in EXTENSIONS:
            continue

        if len(token) == 1 and token.isdigit():
            continue

        result.append(token)

    return result


def fts_quote(token: str) -> str:
    return '"' + token.replace('"', '""') + '"'


def match_variants(query: str) -> list[tuple[str, str]]:
    tokens = query_tokens(query)
    relaxed = relaxed_tokens(query)

    variants: list[tuple[str, str]] = []

    def add(name: str, expression: str) -> None:
        expression = expression.strip()
        if not expression:
            return

        item = (name, expression)

        if item not in variants:
            variants.append(item)

    if tokens:
        add(
            "tokens_and",
            " ".join(
                fts_quote(token)
                for token in tokens
            ),
        )

        add(
            "tokens_or",
            " OR ".join(
                fts_quote(token)
                for token in tokens
            ),
        )

    if relaxed and relaxed != tokens:
        add(
            "relaxed_and",
            " ".join(
                fts_quote(token)
                for token in relaxed
            ),
        )

        add(
            "relaxed_or",
            " OR ".join(
                fts_quote(token)
                for token in relaxed
            ),
        )

    normalized = normalize_query(query)

    if normalized:
        add(
            "normalized_phrase",
            fts_quote(normalized),
        )

    return variants


def extract_cases(report: Any) -> list[dict[str, Any]]:
    """
    Tolerate several report shapes so this harness consumes the
    existing R1G-R2 artifact rather than depending on one JSON layout.
    """

    candidates: list[dict[str, Any]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            rid = None

            for key in (
                "runtime_id",
                "runtime_document_id",
                "document_id",
                "id",
            ):
                if key in value:
                    try:
                        rid = int(value[key])
                    except Exception:
                        rid = None
                    break

            classification = str(
                value.get(
                    "classification",
                    value.get(
                        "status",
                        value.get(
                            "failure_classification",
                            "",
                        ),
                    ),
                )
            )

            title = value.get(
                "title",
                value.get(
                    "document_title",
                    value.get(
                        "name",
                        "",
                    ),
                ),
            )

            query = value.get(
                "query",
                value.get(
                    "original_query",
                    title,
                ),
            )

            if rid is not None:
                candidates.append(
                    {
                        "runtime_id": rid,
                        "title": str(title or ""),
                        "query": str(query or title or ""),
                        "classification": classification,
                    }
                )

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(report)

    dedup: dict[int, dict[str, Any]] = {}

    for item in candidates:
        rid = int(item["runtime_id"])

        if (
            rid in EXPECTED_FAILURE_IDS
            or rid in EXPECTED_RECOVERABLE_IDS
        ):
            current = dedup.get(rid)

            if current is None:
                dedup[rid] = item
                continue

            # Prefer records carrying a real title/query/classification.
            score_current = sum(
                bool(current.get(key))
                for key in (
                    "title",
                    "query",
                    "classification",
                )
            )

            score_new = sum(
                bool(item.get(key))
                for key in (
                    "title",
                    "query",
                    "classification",
                )
            )

            if score_new > score_current:
                dedup[rid] = item

    return [
        dedup[rid]
        for rid in sorted(dedup)
    ]


def discover_runtime_source(
    conn: sqlite3.Connection,
) -> dict[str, str]:
    """
    Find the canonical runtime document table without assuming the
    exact Pack-1-era schema.
    """

    preferred_tables = (
        "runtime_documents",
        "documents",
        "knowledge_documents",
    )

    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        ORDER BY name
        """
    ).fetchall()

    table_names = [
        str(row["name"])
        for row in rows
    ]

    ordered = list(preferred_tables)

    for table in table_names:
        if table not in ordered:
            ordered.append(table)

    for table in ordered:
        if table not in table_names:
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

        content_col = first_existing(
            (
                "content",
                "text",
                "document_text",
                "extracted_text",
                "body",
            ),
            cols,
        )

        if id_col and (title_col or path_col):
            return {
                "table": table,
                "id": id_col,
                "title": title_col or "",
                "path": path_col or "",
                "content": content_col or "",
            }

    raise RuntimeError(
        "unable to discover runtime document source table"
    )


def load_runtime_rows(
    conn: sqlite3.Connection,
    source: dict[str, str],
    ids: Iterable[int],
) -> dict[int, dict[str, Any]]:
    ids = sorted(set(int(v) for v in ids))

    if not ids:
        return {}

    table = source["table"]
    id_col = source["id"]

    select_parts = [
        f"{qident(id_col)} AS runtime_id"
    ]

    if source["title"]:
        select_parts.append(
            f"{qident(source['title'])} AS title"
        )
    else:
        select_parts.append(
            "'' AS title"
        )

    if source["path"]:
        select_parts.append(
            f"{qident(source['path'])} AS file_path"
        )
    else:
        select_parts.append(
            "'' AS file_path"
        )

    if source["content"]:
        select_parts.append(
            f"{qident(source['content'])} AS content"
        )
    else:
        select_parts.append(
            "'' AS content"
        )

    placeholders = ",".join("?" for _ in ids)

    sql = f"""
        SELECT
            {", ".join(select_parts)}
        FROM {qident(table)}
        WHERE {qident(id_col)}
              IN ({placeholders})
    """

    result: dict[int, dict[str, Any]] = {}

    for row in conn.execute(sql, ids):
        rid = int(row["runtime_id"])

        result[rid] = {
            "runtime_id": rid,
            "title": str(row["title"] or ""),
            "file_path": str(row["file_path"] or ""),
            "content": str(row["content"] or ""),
        }

    return result


def load_chunk_text(
    conn: sqlite3.Connection,
    runtime_id: int,
) -> str:
    if not table_exists(conn, "runtime_chunks_fts"):
        return ""

    cols = columns(
        conn,
        "runtime_chunks_fts",
    )

    required = {
        "chunk_text",
        "document_id",
    }

    if not required.issubset(set(cols)):
        return ""

    rows = conn.execute(
        """
        SELECT chunk_text
        FROM runtime_chunks_fts
        WHERE CAST(document_id AS INTEGER) = ?
        ORDER BY CAST(chunk_id AS INTEGER)
        LIMIT 64
        """,
        (runtime_id,),
    ).fetchall()

    return "\n".join(
        str(row["chunk_text"] or "")
        for row in rows
    )


def create_shadow() -> sqlite3.Connection:
    """
    All shadow indexes live in an in-memory SQLite database.
    Nothing is attached and nothing can be written to production.
    """

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE VIRTUAL TABLE shadow_identity_fts
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
        CREATE VIRTUAL TABLE shadow_combined_fts
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
    shadow: sqlite3.Connection,
    row: dict[str, Any],
) -> None:
    shadow.execute(
        """
        INSERT INTO shadow_identity_fts(
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

    shadow.execute(
        """
        INSERT INTO shadow_combined_fts(
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


def run_fts(
    conn: sqlite3.Connection,
    table: str,
    query: str,
    *,
    limit: int = 25,
) -> dict[str, Any]:
    variants = match_variants(query)

    best: dict[str, Any] | None = None
    attempts: list[dict[str, Any]] = []

    for variant_name, expression in variants:
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

            ids = [
                int(row["runtime_id"])
                for row in rows
            ]

            attempt = {
                "variant": variant_name,
                "expression": expression,
                "result_ids": ids,
                "error": None,
            }

            attempts.append(attempt)

            if rows and best is None:
                best = {
                    "variant": variant_name,
                    "expression": expression,
                    "rows": [
                        {
                            "runtime_id": int(row["runtime_id"]),
                            "score": float(row["score"]),
                        }
                        for row in rows
                    ],
                }

        except sqlite3.Error as exc:
            attempts.append(
                {
                    "variant": variant_name,
                    "expression": expression,
                    "result_ids": [],
                    "error": str(exc),
                }
            )

    return {
        "best": best,
        "attempts": attempts,
    }


def target_rank(
    result: dict[str, Any],
    runtime_id: int,
) -> int | None:
    best_rank = None

    for attempt in result["attempts"]:
        ids = attempt.get(
            "result_ids",
            [],
        )

        try:
            rank = ids.index(runtime_id) + 1
        except ValueError:
            continue

        if best_rank is None or rank < best_rank:
            best_rank = rank

    return best_rank


def token_vocab(
    conn: sqlite3.Connection,
    fts_table: str,
) -> list[str]:
    vocab = "temp_vocab"

    try:
        conn.execute(
            f"DROP TABLE IF EXISTS {qident(vocab)}"
        )
    except sqlite3.Error:
        pass

    conn.execute(
        f"""
        CREATE VIRTUAL TABLE {qident(vocab)}
        USING fts5vocab(
            {qident(fts_table)},
            'row'
        )
        """
    )

    rows = conn.execute(
        f"""
        SELECT term
        FROM {qident(vocab)}
        ORDER BY term
        """
    ).fetchall()

    return [
        str(row["term"])
        for row in rows
    ]


def analyze_tokenization(
    value: str,
) -> dict[str, Any]:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
        CREATE VIRTUAL TABLE token_probe
        USING fts5(
            body,
            tokenize='unicode61'
        )
        """
    )

    conn.execute(
        """
        INSERT INTO token_probe(body)
        VALUES (?)
        """,
        (value,),
    )

    vocab = token_vocab(
        conn,
        "token_probe",
    )

    conn.close()

    return {
        "text": value,
        "python_tokens": query_tokens(value),
        "unicode61_terms": vocab,
    }


def negative_shadow_check(
    shadow: sqlite3.Connection,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for query in NEGATIVE_QUERIES:
        identity = run_fts(
            shadow,
            "shadow_identity_fts",
            query,
            limit=10,
        )

        combined = run_fts(
            shadow,
            "shadow_combined_fts",
            query,
            limit=10,
        )

        identity_hits = max(
            (
                len(a["result_ids"])
                for a in identity["attempts"]
                if not a["error"]
            ),
            default=0,
        )

        combined_hits = max(
            (
                len(a["result_ids"])
                for a in combined["attempts"]
                if not a["error"]
            ),
            default=0,
        )

        results.append(
            {
                "query": query,
                "identity_hits": identity_hits,
                "combined_hits": combined_hits,
            }
        )

    return results


def main() -> int:
    started = time.monotonic()

    print("=" * 72)
    print(" GENESIS RECALL R1G-R3")
    print(" FTS TOKENIZATION + SEARCHABLE-IDENTITY SHADOW CERTIFICATION")
    print("=" * 72)

    if not R1G_R2_REPORT.exists():
        print(
            "FAIL: missing R1G-R2 report:",
            R1G_R2_REPORT,
        )
        return 2

    try:
        report_data = json.loads(
            R1G_R2_REPORT.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        print(
            "FAIL: cannot parse R1G-R2 report:",
            exc,
        )
        return 2

    cases = extract_cases(report_data)

    discovered_ids = {
        int(item["runtime_id"])
        for item in cases
    }

    missing_expected = (
        EXPECTED_FAILURE_IDS
        | EXPECTED_RECOVERABLE_IDS
    ) - discovered_ids

    if missing_expected:
        print(
            "FAIL: R1G-R2 report case extraction incomplete:",
            sorted(missing_expected),
        )
        return 2

    failure_cases = [
        item
        for item in cases
        if int(item["runtime_id"])
        in EXPECTED_FAILURE_IDS
    ]

    control_cases = [
        item
        for item in cases
        if int(item["runtime_id"])
        in EXPECTED_RECOVERABLE_IDS
    ]

    print()
    print("R1G-R2 hard failures :", len(failure_cases))
    print("recoverable controls :", len(control_cases))

    if len(failure_cases) != 9:
        print(
            "FAIL: expected exactly 9 hard failures"
        )
        return 2

    if len(control_cases) != 4:
        print(
            "FAIL: expected exactly 4 recoverable controls"
        )
        return 2

    production = open_ro(DB)

    source = discover_runtime_source(
        production
    )

    print()
    print("=== RUNTIME SOURCE ===")
    print("table   :", source["table"])
    print("id      :", source["id"])
    print("title   :", source["title"] or None)
    print("path    :", source["path"] or None)
    print("content :", source["content"] or None)

    all_ids = sorted(
        EXPECTED_FAILURE_IDS
        | EXPECTED_RECOVERABLE_IDS
    )

    runtime_rows = load_runtime_rows(
        production,
        source,
        all_ids,
    )

    if set(runtime_rows) != set(all_ids):
        print(
            "FAIL: runtime source missing IDs:",
            sorted(
                set(all_ids) - set(runtime_rows)
            ),
        )
        production.close()
        return 2

    case_by_id = {
        int(item["runtime_id"]): item
        for item in cases
    }

    shadow = create_shadow()

    assembled: dict[int, dict[str, Any]] = {}

    for rid in all_ids:
        row = runtime_rows[rid]
        case = case_by_id[rid]

        title = (
            row["title"]
            or case.get("title", "")
        )

        file_path = row["file_path"]

        chunk_text = load_chunk_text(
            production,
            rid,
        )

        # If the runtime table contains content but the FTS query above
        # cannot expose chunks for some schema reason, use the canonical
        # read-only content field only for the shadow combined lane.
        if (
            not chunk_text
            and row.get("content")
        ):
            chunk_text = str(
                row["content"]
            )

        assembled[rid] = {
            "runtime_id": rid,
            "title": title,
            "file_path": file_path,
            "chunk_text": chunk_text,
            "query": (
                case.get("query")
                or title
            ),
            "r1g_r2_classification": case.get(
                "classification",
                "",
            ),
        }

        insert_shadow(
            shadow,
            assembled[rid],
        )

    shadow.commit()

    print()
    print("=== TOKENIZATION PROBES ===")

    token_results = [
        analyze_tokenization(value)
        for value in TOKEN_PROBES
    ]

    token_lines: list[str] = []

    for item in token_results:
        print()
        print("TEXT      :", item["text"])
        print(
            "PYTHON    :",
            item["python_tokens"],
        )
        print(
            "UNICODE61 :",
            item["unicode61_terms"],
        )

        token_lines.extend(
            [
                f"TEXT: {item['text']}",
                "PYTHON: "
                + repr(item["python_tokens"]),
                "UNICODE61: "
                + repr(item["unicode61_terms"]),
                "",
            ]
        )

    TOKEN_REPORT.write_text(
        "\n".join(token_lines),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print(" HARD-FAILURE SHADOW MATRIX")
    print("=" * 72)

    results: list[dict[str, Any]] = []

    for index, rid in enumerate(
        sorted(EXPECTED_FAILURE_IDS),
        start=1,
    ):
        row = assembled[rid]
        query = row["query"]

        identity = run_fts(
            shadow,
            "shadow_identity_fts",
            query,
            limit=25,
        )

        combined = run_fts(
            shadow,
            "shadow_combined_fts",
            query,
            limit=25,
        )

        identity_rank = target_rank(
            identity,
            rid,
        )

        combined_rank = target_rank(
            combined,
            rid,
        )

        title_tokens = query_tokens(
            row["title"]
        )

        q_tokens = query_tokens(
            query
        )

        overlap = sorted(
            set(title_tokens)
            & set(q_tokens)
        )

        result = {
            "runtime_id": rid,
            "title": row["title"],
            "query": query,
            "query_tokens": q_tokens,
            "title_tokens": title_tokens,
            "title_overlap": overlap,
            "chunk_chars": len(
                row["chunk_text"]
            ),
            "identity_rank": identity_rank,
            "combined_rank": combined_rank,
            "identity_recovered": (
                identity_rank is not None
            ),
            "combined_recovered": (
                combined_rank is not None
            ),
            "identity_attempts": identity[
                "attempts"
            ],
            "combined_attempts": combined[
                "attempts"
            ],
        }

        results.append(result)

        print()
        print(
            f"[{index:02d}/09] id={rid}"
        )
        print(
            "title         :",
            row["title"],
        )
        print(
            "query         :",
            query,
        )
        print(
            "query tokens  :",
            q_tokens,
        )
        print(
            "title overlap :",
            overlap,
        )
        print(
            "chunk chars   :",
            len(row["chunk_text"]),
        )
        print(
            "identity rank :",
            identity_rank,
        )
        print(
            "combined rank :",
            combined_rank,
        )

    print()
    print("=" * 72)
    print(" RECOVERABLE CONTROL MATRIX")
    print("=" * 72)

    controls: list[dict[str, Any]] = []

    for rid in sorted(
        EXPECTED_RECOVERABLE_IDS
    ):
        row = assembled[rid]
        query = row["query"]

        identity = run_fts(
            shadow,
            "shadow_identity_fts",
            query,
            limit=25,
        )

        combined = run_fts(
            shadow,
            "shadow_combined_fts",
            query,
            limit=25,
        )

        item = {
            "runtime_id": rid,
            "title": row["title"],
            "query": query,
            "identity_rank": target_rank(
                identity,
                rid,
            ),
            "combined_rank": target_rank(
                combined,
                rid,
            ),
        }

        controls.append(item)

        print()
        print("id            :", rid)
        print("title         :", row["title"])
        print(
            "identity rank :",
            item["identity_rank"],
        )
        print(
            "combined rank :",
            item["combined_rank"],
        )

    print()
    print("=" * 72)
    print(" ADVERSARIAL SHADOW CONTROLS")
    print("=" * 72)

    negatives = negative_shadow_check(
        shadow
    )

    suspicious_negative = 0

    for item in negatives:
        suspicious = (
            item["identity_hits"] > 0
            or item["combined_hits"] > 0
        )

        if suspicious:
            suspicious_negative += 1

        print()
        print("query         :", item["query"])
        print(
            "identity hits :",
            item["identity_hits"],
        )
        print(
            "combined hits :",
            item["combined_hits"],
        )

    identity_recovered = sum(
        1
        for item in results
        if item["identity_recovered"]
    )

    combined_recovered = sum(
        1
        for item in results
        if item["combined_recovered"]
    )

    identity_pct = (
        100.0
        * identity_recovered
        / len(results)
        if results
        else 0.0
    )

    combined_pct = (
        100.0
        * combined_recovered
        / len(results)
        if results
        else 0.0
    )

    control_identity = sum(
        1
        for item in controls
        if item["identity_rank"] is not None
    )

    control_combined = sum(
        1
        for item in controls
        if item["combined_rank"] is not None
    )

    # Certification intentionally does NOT require an arbitrary
    # recovery percentage. This pack is diagnostic/certifying:
    # it must faithfully measure all nine known hard failures,
    # preserve the four controls, and produce no adversarial hits.
    shadow_certified = (
        len(results) == 9
        and len(controls) == 4
        and suspicious_negative == 0
    )

    elapsed = time.monotonic() - started

    summary = {
        "pack": "Genesis Recall R1G-R3",
        "purpose": (
            "FTS tokenization and searchable-identity "
            "shadow certification"
        ),
        "production_db_writes": 0,
        "production_source_changes": 0,
        "shadow_database": ":memory:",
        "runtime_source": source,
        "hard_failures_tested": len(results),
        "recoverable_controls_tested": len(
            controls
        ),
        "identity_recovered": identity_recovered,
        "identity_recovery_pct": identity_pct,
        "combined_recovered": combined_recovered,
        "combined_recovery_pct": combined_pct,
        "control_identity_recovered": control_identity,
        "control_combined_recovered": control_combined,
        "negative_queries": len(negatives),
        "suspicious_negative": suspicious_negative,
        "shadow_certified": shadow_certified,
        "elapsed_seconds": elapsed,
        "tokenization": token_results,
        "hard_failure_results": results,
        "controls": controls,
        "negative_results": negatives,
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
                    "runtime_id",
                    "title",
                    "query",
                    "identity_rank",
                    "combined_rank",
                    "chunk_chars",
                )
            )
            + "\n"
        )

        for item in results:
            fh.write(
                "\t".join(
                    (
                        str(item["runtime_id"]),
                        item["title"].replace(
                            "\t",
                            " ",
                        ),
                        item["query"].replace(
                            "\t",
                            " ",
                        ),
                        str(
                            item["identity_rank"]
                            or ""
                        ),
                        str(
                            item["combined_rank"]
                            or ""
                        ),
                        str(item["chunk_chars"]),
                    )
                )
                + "\n"
            )

    print()
    print("=" * 72)
    print(" R1G-R3 SHADOW RESULT")
    print("=" * 72)
    print(
        "hard failures tested      :",
        len(results),
    )
    print(
        "identity recovered        :",
        f"{identity_recovered}/9 "
        f"({identity_pct:.1f}%)",
    )
    print(
        "combined recovered        :",
        f"{combined_recovered}/9 "
        f"({combined_pct:.1f}%)",
    )
    print(
        "recoverable controls      :",
        len(controls),
    )
    print(
        "control identity recovered:",
        f"{control_identity}/4",
    )
    print(
        "control combined recovered:",
        f"{control_combined}/4",
    )
    print(
        "adversarial queries       :",
        len(negatives),
    )
    print(
        "suspicious negatives      :",
        suspicious_negative,
    )
    print(
        "shadow certified          :",
        shadow_certified,
    )
    print(
        "elapsed seconds           :",
        f"{elapsed:.2f}",
    )
    print("=" * 72)

    production.close()
    shadow.close()

    if not shadow_certified:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
