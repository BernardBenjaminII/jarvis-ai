from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import statistics
import time

from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "genesis-recall-r1f-r5-v1"

SAMPLE_SIZE = 100

R1F_REASON = (
    "complete_core_term_coverage_strong_subject"
)


# ============================================================
# TOKEN / QUERY RULES
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


def build_query(
    title: str,
) -> str | None:
    """
    Deterministically derive a compact catalog-awareness query.

    This is deliberately NOT the complete exact title.

    Prefer informative title tokens, but preserve their original
    order so the query remains human-auditable.
    """

    terms = tokenize(title)

    if len(terms) < 2:
        return None

    scored = []

    for index, token in enumerate(
        terms
    ):

        folded = token.casefold()

        alpha = sum(
            char.isalpha()
            for char in token
        )

        digit = sum(
            char.isdigit()
            for char in token
        )

        score = (
            min(len(token), 20)
            + alpha
            - min(digit, 5)
        )

        # Useful technical syntax deserves to survive.
        if any(
            marker in token
            for marker in (
                "++",
                "#",
                ".",
            )
        ):
            score += 3

        scored.append(
            (
                -score,
                index,
                token,
            )
        )

    scored.sort()

    selected = scored[:4]

    selected.sort(
        key=lambda item: item[1]
    )

    query = " ".join(
        item[2]
        for item in selected
    ).strip()

    if len(tokenize(query)) < 2:
        return None

    return query


# ============================================================
# DATABASE
# ============================================================

def open_read_only(
    path: Path,
) -> sqlite3.Connection:

    connection = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    connection.row_factory = (
        sqlite3.Row
    )

    connection.execute(
        "PRAGMA query_only=ON"
    )

    connection.execute(
        "PRAGMA busy_timeout=10000"
    )

    return connection


def table_exists(
    connection: sqlite3.Connection,
    table: str,
) -> bool:

    row = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        LIMIT 1
        """,
        (table,),
    ).fetchone()

    return row is not None


# ============================================================
# ELIGIBLE UNIVERSE
# ============================================================

def build_eligible_universe(
    connection: sqlite3.Connection,
) -> tuple[
    list[dict[str, Any]],
    dict[str, int],
]:
    """
    Build the universe BEFORE sampling.

    Eligibility:
      - runtime document exists
      - >= 500 extracted characters
      - at least one runtime chunk
      - usable title
      - deterministic query can be generated

    We intentionally do not require that search can already find
    the document. That is what the census is measuring.
    """

    total_runtime = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM runtime_documents
            """
        ).fetchone()[0]
    )

    content_eligible = int(
        connection.execute(
            """
            SELECT COUNT(*)
            FROM runtime_documents
            WHERE content_chars >= 500
            """
        ).fetchone()[0]
    )

    chunked = int(
        connection.execute(
            """
            SELECT COUNT(DISTINCT rd.id)
            FROM runtime_documents rd
            WHERE rd.content_chars >= 500
              AND EXISTS (
                  SELECT 1
                  FROM runtime_chunks rc
                  WHERE rc.document_id = rd.id
              )
            """
        ).fetchone()[0]
    )

    rows = connection.execute(
        """
        SELECT
            rd.id,
            rd.title,
            rd.file_path,
            rd.media_type,
            rd.content_chars,
            (
                SELECT COUNT(*)
                FROM runtime_chunks rc
                WHERE rc.document_id = rd.id
            ) AS chunk_count
        FROM runtime_documents rd
        WHERE rd.content_chars >= 500
          AND EXISTS (
              SELECT 1
              FROM runtime_chunks rc
              WHERE rc.document_id = rd.id
          )
        ORDER BY rd.id
        """
    ).fetchall()

    eligible: list[
        dict[str, Any]
    ] = []

    unusable_title = 0
    unusable_query = 0

    for row in rows:

        item = dict(row)

        title = str(
            item.get("title")
            or ""
        ).strip()

        if not title:
            unusable_title += 1
            continue

        query = build_query(
            title
        )

        if not query:
            unusable_query += 1
            continue

        item[
            "benchmark_query"
        ] = query

        eligible.append(
            item
        )

    stats = {
        "runtime_documents":
            total_runtime,

        "content_eligible":
            content_eligible,

        "content_and_chunk_eligible":
            chunked,

        "unusable_title":
            unusable_title,

        "unusable_query":
            unusable_query,

        "eligible_universe":
            len(eligible),
    }

    return eligible, stats


# ============================================================
# DETERMINISTIC QUANTILE SAMPLE
# ============================================================

def deterministic_quantile_sample(
    universe: list[dict[str, Any]],
    sample_size: int,
) -> list[dict[str, Any]]:
    """
    Select exactly one item from each equal quantile of the
    already-constructed eligible universe.

    No forward searching.
    No repeated convergence.
    No post-selection deduplication.
    """

    population = len(
        universe
    )

    if population < sample_size:
        return []

    if sample_size == 1:
        return [
            universe[
                population // 2
            ]
        ]

    indexes: list[int] = []

    for bucket in range(
        sample_size
    ):

        # Midpoint of each equal population bucket.
        position = (
            (
                bucket + 0.5
            )
            * population
            / sample_size
        )

        index = int(position)

        if index >= population:
            index = population - 1

        indexes.append(
            index
        )

    # With population >= sample_size and equal quantile
    # midpoints, these should always be unique.
    if len(set(indexes)) != sample_size:
        raise RuntimeError(
            "quantile selection produced duplicate indexes"
        )

    return [
        universe[index]
        for index in indexes
    ]


# ============================================================
# SEARCH RESULT HELPERS
# ============================================================

def result_runtime_id(
    row: dict[str, Any],
) -> int | None:

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
            continue

    return None


def result_path(
    row: dict[str, Any],
) -> str | None:

    for key in (
        "file_path",
        "source_path",
        "document_path",
        "path",
    ):

        value = row.get(key)

        if value:
            return str(value)

    return None


def is_expected(
    row: dict[str, Any],
    *,
    runtime_id: int,
    expected_path: str,
) -> bool:

    rid = result_runtime_id(
        row
    )

    if rid == runtime_id:
        return True

    path = result_path(
        row
    )

    return bool(
        path
        and path == expected_path
    )


def expected_rank(
    rows: list[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        if is_expected(
            row,
            runtime_id=runtime_id,
            expected_path=expected_path,
        ):
            return rank

    return None


def expected_row(
    rows: list[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> dict[str, Any] | None:

    for row in rows:

        if is_expected(
            row,
            runtime_id=runtime_id,
            expected_path=expected_path,
        ):
            return row

    return None


# ============================================================
# QUALIFICATION DIAGNOSTICS
# ============================================================

def enum_value(
    value: Any,
) -> str | None:

    if value is None:
        return None

    return str(
        getattr(
            value,
            "value",
            value,
        )
    )


def evidence_path(
    evidence: Any,
) -> str:

    candidate = getattr(
        evidence,
        "candidate",
        None,
    )

    if candidate is None:
        return ""

    return str(
        getattr(
            candidate,
            "source_path",
            "",
        )
        or ""
    )


def evidence_score(
    evidence: Any,
) -> dict[str, float]:

    score = getattr(
        evidence,
        "score",
        None,
    )

    output: dict[
        str,
        float,
    ] = {}

    for name in (
        "lexical",
        "semantic",
        "phrase",
        "entity",
        "subject",
        "provenance",
        "confidence",
        "final",
    ):

        try:
            value = getattr(
                score,
                name,
                None,
            )

            if value is None:
                continue

            output[name] = float(
                value
            )

        except Exception:
            continue

    return output


def diagnose_qualification_drop(
    *,
    query: str,
    raw_rows: list[dict[str, Any]],
    expected_path: str,
    qualify_rows: Any,
    rescue_fn: Any,
    engine: Any,
) -> dict[str, Any]:

    _, qualification = (
        qualify_rows(
            query,
            raw_rows,
            engine=engine,
        )
    )

    target = None

    for evidence in (
        list(
            qualification.accepted
        )
        + list(
            qualification.rejected
        )
    ):

        if (
            evidence_path(evidence)
            == expected_path
        ):
            target = evidence
            break

    if target is None:

        return {
            "status":
                "QUALIFICATION_EVIDENCE_NOT_FOUND",
        }

    decision = enum_value(
        getattr(
            target,
            "decision",
            None,
        )
    )

    rescue = None
    rescue_reason = None

    if decision != "accepted":

        rescue, rescue_reason = (
            rescue_fn(
                query,
                target,
                threshold=float(
                    qualification.threshold
                ),
            )
        )

    return {
        "status":
            "FOUND",

        "decision":
            decision,

        "explanation":
            getattr(
                target,
                "explanation",
                None,
            ),

        "threshold":
            float(
                qualification.threshold
            ),

        "score":
            evidence_score(
                target
            ),

        "rescue":
            rescue,

        "rescue_reason":
            rescue_reason,
    }


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(
    raw_rank: int | None,
    qualified_rank: int | None,
) -> str:

    if raw_rank is None:
        return "RAW_RETRIEVAL_MISS"

    if raw_rank > 20:
        return "RAW_HIT_BAD_RANK"

    if qualified_rank is None:
        return "QUALIFICATION_DROP"

    if qualified_rank > 20:
        return "QUALIFIED_BAD_RANK"

    return "QUALIFIED_RECALL_PASS"


# ============================================================
# BENCHMARK ONE DOCUMENT
# ============================================================

def benchmark_document(
    *,
    expected: dict[str, Any],
    db_path: Path,
    search_catalog: Any,
    search_qualified_catalog: Any,
    qualify_rows: Any,
    rescue_fn: Any,
    engine: Any,
    limit: int,
) -> dict[str, Any]:

    query = str(
        expected[
            "benchmark_query"
        ]
    )

    runtime_id = int(
        expected["id"]
    )

    expected_path = str(
        expected["file_path"]
    )

    raw_rows = list(
        search_catalog(
            query,
            db_path=db_path,
            limit=limit,
        )
    )

    qualified_rows = list(
        search_qualified_catalog(
            query,
            db_path=db_path,
            limit=limit,
            engine=engine,
        )
    )

    raw_rank = expected_rank(
        raw_rows,
        runtime_id=runtime_id,
        expected_path=expected_path,
    )

    qualified_rank = expected_rank(
        qualified_rows,
        runtime_id=runtime_id,
        expected_path=expected_path,
    )

    qrow = expected_row(
        qualified_rows,
        runtime_id=runtime_id,
        expected_path=expected_path,
    )

    status = classify(
        raw_rank,
        qualified_rank,
    )

    diagnosis = None

    if (
        raw_rank is not None
        and qualified_rank is None
    ):

        diagnosis = (
            diagnose_qualification_drop(
                query=query,
                raw_rows=raw_rows,
                expected_path=
                    expected_path,
                qualify_rows=
                    qualify_rows,
                rescue_fn=
                    rescue_fn,
                engine=engine,
            )
        )

    return {
        "runtime_id":
            runtime_id,

        "title":
            expected["title"],

        "file_path":
            expected_path,

        "media_type":
            expected["media_type"],

        "content_chars":
            int(
                expected[
                    "content_chars"
                ]
            ),

        "chunk_count":
            int(
                expected[
                    "chunk_count"
                ]
            ),

        "query":
            query,

        "raw_count":
            len(raw_rows),

        "raw_rank":
            raw_rank,

        "qualified_count":
            len(
                qualified_rows
            ),

        "qualified_rank":
            qualified_rank,

        "status":
            status,

        "qualification_decision":
            (
                qrow.get(
                    "qualification_decision"
                )
                if qrow
                else None
            ),

        "qualification_rescue":
            (
                qrow.get(
                    "qualification_rescue"
                )
                if qrow
                else None
            ),

        "qualification_rescue_reason":
            (
                qrow.get(
                    "qualification_rescue_reason"
                )
                if qrow
                else None
            ),

        "drop_diagnosis":
            diagnosis,
    }


# ============================================================
# METRICS
# ============================================================

def count_at(
    rows: Iterable[
        dict[str, Any]
    ],
    field: str,
    k: int,
) -> int:

    count = 0

    for row in rows:

        value = row.get(
            field
        )

        if value is None:
            continue

        if int(value) <= k:
            count += 1

    return count


def percentage(
    value: int,
    total: int,
) -> float:

    if total <= 0:
        return 0.0

    return (
        value
        * 100.0
        / total
    )


def grade(
    qualified_at_5: int,
    total: int,
) -> str:

    if total != SAMPLE_SIZE:
        return "INVALID_SAMPLE"

    pct = percentage(
        qualified_at_5,
        total,
    )

    if pct >= 95.0:
        return "EXCELLENT"

    if pct >= 90.0:
        return "STRONG"

    if pct >= 80.0:
        return "NEEDS_IMPROVEMENT"

    return "RECALL_DEFICIENT"


# ============================================================
# REPORT OUTPUT
# ============================================================

def write_tsv(
    path: Path,
    rows: list[dict[str, Any]],
) -> None:

    fields = (
        "sample_number",
        "runtime_id",
        "media_type",
        "content_chars",
        "chunk_count",
        "query",
        "raw_rank",
        "qualified_rank",
        "status",
        "qualification_decision",
        "qualification_rescue_reason",
        "title",
        "file_path",
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

        for row in rows:
            writer.writerow(
                row
            )


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
        "--report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--sample-report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--sample-size",
        type=int,
        default=SAMPLE_SIZE,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=25,
    )

    args = parser.parse_args()

    if args.sample_size != SAMPLE_SIZE:

        print(
            "FAIL: R1F-R5 certification "
            "requires sample-size=100"
        )

        return 2

    if not args.db.is_file():

        print(
            "FAIL: runtime DB missing"
        )

        return 2


    from core.knowledge_catalog.search import (
        search_catalog,
    )

    from core.knowledge_catalog.qualified_search import (
        search_qualified_catalog,
        qualify_rows,
        _gate_repair_should_rescue,
    )

    from core.retrieval.qualification.evaluator import (
        QualificationEngine,
    )


    started = time.monotonic()

    connection = open_read_only(
        args.db
    )

    engine = QualificationEngine()


    try:

        print(
            "============================================================"
        )

        print(
            " GENESIS RECALL R1F-R5"
        )

        print(
            " DETERMINISTIC 100-DOCUMENT RECALL CENSUS"
        )

        print(
            "============================================================"
        )


        # ====================================================
        # 1. SCHEMA
        # ====================================================

        print()
        print(
            "=== 1. RUNTIME SCHEMA CONTRACT ==="
        )

        required = (
            "runtime_documents",
            "runtime_chunks",
        )

        for table in required:

            exists = table_exists(
                connection,
                table,
            )

            print(
                f"{table:24} : "
                f"{'PASS' if exists else 'MISSING'}"
            )

            if not exists:
                return 3


        # ====================================================
        # 2. BUILD ELIGIBLE UNIVERSE
        # ====================================================

        print()
        print(
            "=== 2. BUILD ELIGIBLE RECALL UNIVERSE ==="
        )

        universe, universe_stats = (
            build_eligible_universe(
                connection
            )
        )

        print(
            "runtime documents          :",
            f"{universe_stats['runtime_documents']:,}",
        )

        print(
            "content >=500              :",
            f"{universe_stats['content_eligible']:,}",
        )

        print(
            "content + runtime chunks   :",
            f"{universe_stats['content_and_chunk_eligible']:,}",
        )

        print(
            "unusable title             :",
            f"{universe_stats['unusable_title']:,}",
        )

        print(
            "unusable generated query   :",
            f"{universe_stats['unusable_query']:,}",
        )

        print(
            "eligible recall universe   :",
            f"{universe_stats['eligible_universe']:,}",
        )


        # ====================================================
        # 3. EXACT DETERMINISTIC SAMPLE
        # ====================================================

        print()
        print(
            "=== 3. DETERMINISTIC QUANTILE SAMPLE ==="
        )

        sample = (
            deterministic_quantile_sample(
                universe,
                args.sample_size,
            )
        )

        print(
            "requested sample :",
            args.sample_size,
        )

        print(
            "selected sample  :",
            len(sample),
        )

        sample_ids = [
            int(
                item["id"]
            )
            for item in sample
        ]

        unique_ids = len(
            set(sample_ids)
        )

        print(
            "unique IDs       :",
            unique_ids,
        )

        if (
            len(sample)
            != args.sample_size
        ):

            print(
                "FAIL: exact 100-document "
                "sample not available"
            )

            print(
                "CORPUS GRADE: INVALID_SAMPLE"
            )

            report = {
                "schema":
                    SCHEMA_VERSION,

                "read_only":
                    True,

                "universe":
                    universe_stats,

                "sample": {
                    "requested":
                        args.sample_size,

                    "selected":
                        len(sample),

                    "unique_ids":
                        unique_ids,

                    "valid":
                        False,
                },

                "certification": {
                    "certified":
                        False,

                    "reason":
                        "EXACT_SAMPLE_NOT_AVAILABLE",
                },
            }

            args.report.write_text(
                json.dumps(
                    report,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )

            return 4


        if unique_ids != args.sample_size:

            print(
                "FAIL: duplicate IDs "
                "in deterministic sample"
            )

            return 4


        print(
            "PASS: exact 100-document "
            "sample constructed"
        )

        print(
            "minimum sampled ID :",
            min(sample_ids),
        )

        print(
            "maximum sampled ID :",
            max(sample_ids),
        )


        # ====================================================
        # 4. RUN RECALL CENSUS
        # ====================================================

        print()
        print(
            "=== 4. PRODUCTION RECALL CENSUS ==="
        )

        results: list[
            dict[str, Any]
        ] = []

        for number, expected in enumerate(
            sample,
            start=1,
        ):

            result = benchmark_document(
                expected=expected,
                db_path=args.db,
                search_catalog=
                    search_catalog,
                search_qualified_catalog=
                    search_qualified_catalog,
                qualify_rows=
                    qualify_rows,
                rescue_fn=
                    _gate_repair_should_rescue,
                engine=engine,
                limit=args.limit,
            )

            result[
                "sample_number"
            ] = number

            results.append(
                result
            )

            print(
                f"[{number:03d}/100] "
                f"id={result['runtime_id']:<7} "
                f"raw={str(result['raw_rank']):<4} "
                f"qual={str(result['qualified_rank']):<4} "
                f"{result['status']}"
            )

            print(
                "          query:",
                result["query"],
            )

            if (
                result["status"]
                == "QUALIFICATION_DROP"
            ):

                diagnosis = (
                    result.get(
                        "drop_diagnosis"
                    )
                    or {}
                )

                print(
                    "          decision:",
                    diagnosis.get(
                        "decision"
                    ),
                )

                print(
                    "          reason  :",
                    diagnosis.get(
                        "explanation"
                    ),
                )

                print(
                    "          rescue  :",
                    diagnosis.get(
                        "rescue"
                    ),
                    diagnosis.get(
                        "rescue_reason"
                    ),
                )


        # ====================================================
        # 5. CLASSIFICATION COUNTS
        # ====================================================

        print()
        print(
            "=== 5. FAILURE BOUNDARY CLASSIFICATION ==="
        )

        status_counts = Counter(
            row["status"]
            for row in results
        )

        classifications = (
            "RAW_RETRIEVAL_MISS",
            "RAW_HIT_BAD_RANK",
            "QUALIFICATION_DROP",
            "QUALIFIED_BAD_RANK",
            "QUALIFIED_RECALL_PASS",
        )

        for name in classifications:

            print(
                f"{name:28} : "
                f"{status_counts.get(name, 0)}"
            )


        # ====================================================
        # 6. RECALL METRICS
        # ====================================================

        total = len(
            results
        )

        raw1 = count_at(
            results,
            "raw_rank",
            1,
        )

        raw5 = count_at(
            results,
            "raw_rank",
            5,
        )

        raw20 = count_at(
            results,
            "raw_rank",
            20,
        )

        qualified1 = count_at(
            results,
            "qualified_rank",
            1,
        )

        qualified5 = count_at(
            results,
            "qualified_rank",
            5,
        )

        qualified20 = count_at(
            results,
            "qualified_rank",
            20,
        )

        raw_found = sum(
            1
            for row in results
            if row["raw_rank"]
            is not None
        )

        qualified_found = sum(
            1
            for row in results
            if row["qualified_rank"]
            is not None
        )

        corpus_grade = grade(
            qualified5,
            total,
        )


        # ====================================================
        # 7. QUALIFICATION DROP REASONS
        # ====================================================

        print()
        print(
            "=== 6. QUALIFICATION DROP ANALYSIS ==="
        )

        drop_reasons = Counter()

        drops = [
            row
            for row in results
            if row["status"]
            == "QUALIFICATION_DROP"
        ]

        for row in drops:

            diagnosis = (
                row.get(
                    "drop_diagnosis"
                )
                or {}
            )

            reason = (
                diagnosis.get(
                    "decision"
                )
                or diagnosis.get(
                    "status"
                )
                or "UNKNOWN"
            )

            drop_reasons[
                reason
            ] += 1

        print(
            "qualification drops :",
            len(drops),
        )

        if not drop_reasons:
            print(
                "drop reasons        : NONE"
            )

        for reason, count in (
            drop_reasons.most_common()
        ):

            print(
                f"  {reason:36} : {count}"
            )


        # ====================================================
        # 8. R1F RESCUE USAGE
        # ====================================================

        print()
        print(
            "=== 7. R1F RESCUE OBSERVATION ==="
        )

        r1f_rescues = [
            row
            for row in results
            if row.get(
                "qualification_rescue_reason"
            )
            == R1F_REASON
        ]

        all_rescues = [
            row
            for row in results
            if row.get(
                "qualification_rescue"
            )
        ]

        print(
            "all production rescues :",
            len(all_rescues),
        )

        print(
            "R1F new-path rescues    :",
            len(r1f_rescues),
        )

        for row in r1f_rescues[:20]:

            print(
                f"  id={row['runtime_id']} "
                f"rank={row['qualified_rank']} "
                f"{row['title']}"
            )


        # ====================================================
        # 9. QUERY / SAMPLE DISTRIBUTION
        # ====================================================

        print()
        print(
            "=== 8. SAMPLE DISTRIBUTION ==="
        )

        content_sizes = [
            int(
                row["content_chars"]
            )
            for row in results
        ]

        chunk_counts = [
            int(
                row["chunk_count"]
            )
            for row in results
        ]

        print(
            "sample min runtime ID :",
            min(
                row["runtime_id"]
                for row in results
            ),
        )

        print(
            "sample max runtime ID :",
            max(
                row["runtime_id"]
                for row in results
            ),
        )

        print(
            "median content chars  :",
            int(
                statistics.median(
                    content_sizes
                )
            ),
        )

        print(
            "median chunk count    :",
            int(
                statistics.median(
                    chunk_counts
                )
            ),
        )


        # ====================================================
        # 10. FINAL CENSUS
        # ====================================================

        print()
        print(
            "============================================================"
        )

        print(
            " JARVIS DETERMINISTIC RECALL CENSUS"
        )

        print(
            "============================================================"
        )

        print()
        print(
            "ELIGIBLE UNIVERSE"
        )

        print(
            f"  runtime documents       : "
            f"{universe_stats['runtime_documents']:,}"
        )

        print(
            f"  content >=500           : "
            f"{universe_stats['content_eligible']:,}"
        )

        print(
            f"  content + chunks        : "
            f"{universe_stats['content_and_chunk_eligible']:,}"
        )

        print(
            f"  recall-eligible         : "
            f"{universe_stats['eligible_universe']:,}"
        )


        print()
        print(
            "SAMPLE VALIDITY"
        )

        print(
            f"  requested               : {args.sample_size}"
        )

        print(
            f"  selected                : {total}"
        )

        print(
            f"  unique                  : "
            f"{len(set(row['runtime_id'] for row in results))}"
        )

        print(
            "  deterministic           : YES"
        )

        print(
            "  exact sample            : PASS"
        )


        print()
        print(
            "RAW RETRIEVAL"
        )

        print(
            f"  found anywhere          : "
            f"{raw_found}/{total} "
            f"({percentage(raw_found, total):.1f}%)"
        )

        print(
            f"  recall @1               : "
            f"{raw1}/{total} "
            f"({percentage(raw1, total):.1f}%)"
        )

        print(
            f"  recall @5               : "
            f"{raw5}/{total} "
            f"({percentage(raw5, total):.1f}%)"
        )

        print(
            f"  recall @20              : "
            f"{raw20}/{total} "
            f"({percentage(raw20, total):.1f}%)"
        )


        print()
        print(
            "QUALIFIED RETRIEVAL"
        )

        print(
            f"  found anywhere          : "
            f"{qualified_found}/{total} "
            f"({percentage(qualified_found, total):.1f}%)"
        )

        print(
            f"  recall @1               : "
            f"{qualified1}/{total} "
            f"({percentage(qualified1, total):.1f}%)"
        )

        print(
            f"  recall @5               : "
            f"{qualified5}/{total} "
            f"({percentage(qualified5, total):.1f}%)"
        )

        print(
            f"  recall @20              : "
            f"{qualified20}/{total} "
            f"({percentage(qualified20, total):.1f}%)"
        )


        print()
        print(
            "FAILURE BOUNDARIES"
        )

        for name in classifications:

            print(
                f"  {name:26} : "
                f"{status_counts.get(name, 0)}"
            )


        print()
        print(
            "QUALIFICATION"
        )

        print(
            f"  raw-hit qualification drops : "
            f"{len(drops)}"
        )

        print(
            f"  production rescues           : "
            f"{len(all_rescues)}"
        )

        print(
            f"  R1F new-path rescues         : "
            f"{len(r1f_rescues)}"
        )


        print()
        print(
            "CORPUS RECALL GRADE"
        )

        print(
            f"  qualified recall @5     : "
            f"{percentage(qualified5, total):.1f}%"
        )

        print(
            f"  grade                   : "
            f"{corpus_grade}"
        )


        # ====================================================
        # CERTIFICATION SEMANTICS
        #
        # Certification means the census itself is valid and
        # production remained read-only.
        #
        # It DOES NOT mean recall quality is acceptable.
        # ====================================================

        census_valid = (
            total == SAMPLE_SIZE
            and len(
                set(
                    row["runtime_id"]
                    for row in results
                )
            )
            == SAMPLE_SIZE
        )

        print()
        print(
            "CENSUS VALIDITY"
        )

        print(
            "  exact 100 sample        :",
            "PASS"
            if census_valid
            else "FAIL",
        )

        print(
            "  quality interpretation  :",
            corpus_grade,
        )


        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print(
            f"elapsed seconds          : "
            f"{elapsed:.2f}"
        )

        print(
            "production DB writes     : 0"
        )

        print(
            "production source changes: 0"
        )

        print(
            "============================================================"
        )


        # ====================================================
        # WRITE REPORTS
        # ====================================================

        report = {
            "schema":
                SCHEMA_VERSION,

            "read_only":
                True,

            "universe":
                universe_stats,

            "sample": {
                "requested":
                    args.sample_size,

                "selected":
                    total,

                "unique_ids":
                    len(
                        set(
                            row[
                                "runtime_id"
                            ]
                            for row
                            in results
                        )
                    ),

                "deterministic":
                    True,

                "valid":
                    census_valid,
            },

            "raw_retrieval": {
                "found_anywhere":
                    raw_found,

                "recall_at_1":
                    raw1,

                "recall_at_5":
                    raw5,

                "recall_at_20":
                    raw20,

                "found_percentage":
                    percentage(
                        raw_found,
                        total,
                    ),

                "recall_at_5_percentage":
                    percentage(
                        raw5,
                        total,
                    ),
            },

            "qualified_retrieval": {
                "found_anywhere":
                    qualified_found,

                "recall_at_1":
                    qualified1,

                "recall_at_5":
                    qualified5,

                "recall_at_20":
                    qualified20,

                "found_percentage":
                    percentage(
                        qualified_found,
                        total,
                    ),

                "recall_at_5_percentage":
                    percentage(
                        qualified5,
                        total,
                    ),
            },

            "failure_boundaries":
                dict(
                    status_counts
                ),

            "qualification": {
                "drops":
                    len(drops),

                "drop_reasons":
                    dict(
                        drop_reasons
                    ),

                "production_rescues":
                    len(
                        all_rescues
                    ),

                "r1f_new_path_rescues":
                    len(
                        r1f_rescues
                    ),
            },

            "quality": {
                "grade":
                    corpus_grade,
            },

            "results":
                results,

            "elapsed_seconds":
                elapsed,

            "certification": {
                "census_valid":
                    census_valid,

                "certified":
                    census_valid,
            },
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

        write_tsv(
            args.sample_report,
            results,
        )

        print()
        print(
            "JSON report:",
            args.report,
        )

        print(
            "TSV sample :",
            args.sample_report,
        )

        return (
            0
            if census_valid
            else 1
        )


    finally:

        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
