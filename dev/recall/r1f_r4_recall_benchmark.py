from __future__ import annotations

import argparse
import json
import math
import re
import sqlite3
import time

from collections import Counter
from pathlib import Path
from typing import Any


# ============================================================
# KNOWN SEMANTIC CANARIES
# ============================================================

KNOWN = (
    {
        "name": "ai_assisted_python",
        "query": "AI assisted Python programming",
        "runtime_id": 11,
        "expect_r1f": True,
    },
    {
        "name": "cpp_programming",
        "query": "C++ programming",
        "runtime_id": 4,
        "expect_r1f": False,
    },
    {
        "name": "effective_c",
        "query": "effective C programming",
        "runtime_id": 14,
        "expect_r1f": False,
    },
    {
        "name": "civil_defense",
        "query": "civil defense manual",
        "runtime_id": 18,
        "expect_r1f": False,
    },
    {
        "name": "army_survival",
        "query": "US Army survival manual",
        "runtime_id": 32,
        "expect_r1f": False,
    },
    {
        "name": "practical_electronics",
        "query": "practical electronics handbook",
        "runtime_id": 42,
        "expect_r1f": False,
    },
    {
        "name": "marx_mathematics",
        "query": "Marx mathematical manuscripts",
        "runtime_id": 89330,
        "expect_r1f": False,
    },
)


# ============================================================
# ADVERSARIAL / NONSENSE CONTROLS
#
# They need not necessarily produce zero normal results.
#
# What MUST remain zero is use of the new R1F rescue reason.
# ============================================================

NEGATIVE = (
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


R1F_REASON = (
    "complete_core_term_coverage_strong_subject"
)


# ============================================================
# TITLE QUERY CONSTRUCTION
# ============================================================

TOKEN_RE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9+#._-]{1,}"
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "this",
    "that",
    "your",
    "using",
    "used",
    "book",
    "books",
    "guide",
    "manual",
    "edition",
    "volume",
    "part",
    "file",
    "document",
    "documents",
    "introduction",
    "complete",
    "updated",
    "final",
    "series",
}


def tokens(text: str) -> list[str]:

    output = []

    for match in TOKEN_RE.finditer(
        text
    ):
        token = match.group(0).strip(
            "._-"
        )

        if len(token) < 2:
            continue

        if token.casefold() in STOPWORDS:
            continue

        if token.casefold() not in {
            item.casefold()
            for item in output
        }:
            output.append(token)

    return output


def title_query(title: str) -> str | None:

    terms = tokens(title)

    if len(terms) < 3:
        return None

    # Prefer informative/longer tokens while keeping the
    # resulting query compact.
    ranked = sorted(
        terms,
        key=lambda value: (
            -len(value),
            terms.index(value),
        ),
    )

    chosen = ranked[:4]

    # Restore original title order.
    chosen.sort(
        key=lambda value:
            terms.index(value)
    )

    return " ".join(chosen)


# ============================================================
# DATABASE
# ============================================================

def ro(
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


def runtime_document(
    connection: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any] | None:

    row = connection.execute(
        """
        SELECT
            id,
            title,
            file_path,
            media_type,
            content_chars
        FROM runtime_documents
        WHERE id=?
        LIMIT 1
        """,
        (runtime_id,),
    ).fetchone()

    return (
        dict(row)
        if row is not None
        else None
    )


# ============================================================
# RESULT NORMALIZATION
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
            pass

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


def rank_expected(
    rows: list[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        if (
            result_runtime_id(row)
            == runtime_id
        ):
            return rank

        path = result_path(row)

        if (
            path
            and path == expected_path
        ):
            return rank

    return None


def expected_result(
    rows: list[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> dict[str, Any] | None:

    for row in rows:

        if (
            result_runtime_id(row)
            == runtime_id
        ):
            return row

        path = result_path(row)

        if (
            path
            and path == expected_path
        ):
            return row

    return None


# ============================================================
# QUALIFICATION DROP DIAGNOSTIC
# ============================================================

def decision_value(
    evidence: Any,
) -> str:

    value = getattr(
        evidence,
        "decision",
        None,
    )

    return str(
        getattr(
            value,
            "value",
            value,
        )
    )


def candidate_path(
    evidence: Any,
) -> str:

    candidate = evidence.candidate

    return str(
        getattr(
            candidate,
            "source_path",
            "",
        )
        or ""
    )


def score_vector(
    evidence: Any,
) -> dict[str, float]:

    output = {}

    score = getattr(
        evidence,
        "score",
        None,
    )

    for name in (
        "lexical",
        "semantic",
        "phrase",
        "entity",
        "subject",
        "provenance",
        "final",
    ):

        try:
            output[name] = float(
                getattr(
                    score,
                    name,
                    0.0,
                )
                or 0.0
            )

        except Exception:
            output[name] = 0.0

    return output


def qualification_diagnosis(
    *,
    query: str,
    raw_rows: list[dict[str, Any]],
    expected_path: str,
    engine: Any,
    qualify_rows: Any,
    rescue_fn: Any,
) -> dict[str, Any]:

    accepted, result = qualify_rows(
        query,
        raw_rows,
        engine=engine,
    )

    target = None

    for evidence in (
        list(result.accepted)
        + list(result.rejected)
    ):

        if (
            candidate_path(evidence)
            == expected_path
        ):
            target = evidence
            break

    if target is None:

        return {
            "status":
                "QUALIFICATION_EVIDENCE_NOT_FOUND",
        }

    decision = decision_value(
        target
    )

    rescue = None
    rescue_reason = None

    if decision != "accepted":

        rescue, rescue_reason = (
            rescue_fn(
                query,
                target,
                threshold=float(
                    result.threshold
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
                result.threshold
            ),

        "score":
            score_vector(
                target
            ),

        "rescue":
            rescue,

        "rescue_reason":
            rescue_reason,
    }


# ============================================================
# STRATIFIED CORPUS SAMPLE
#
# Spread samples across the full runtime ID range rather than
# taking the first 100 records.
# ============================================================

def choose_sample(
    connection: sqlite3.Connection,
    size: int,
) -> list[dict[str, Any]]:

    bounds = connection.execute(
        """
        SELECT
            MIN(id) AS min_id,
            MAX(id) AS max_id
        FROM runtime_documents
        """
    ).fetchone()

    min_id = int(
        bounds["min_id"]
    )

    max_id = int(
        bounds["max_id"]
    )

    targets = []

    if size <= 1:

        targets = [
            min_id
            + (
                max_id - min_id
            )
            // 2
        ]

    else:

        span = (
            max_id
            - min_id
        )

        for index in range(size):

            targets.append(
                min_id
                + round(
                    span
                    * index
                    / (
                        size - 1
                    )
                )
            )

    sample = []

    seen_ids = set()
    seen_titles = set()

    for target in targets:

        cursor = target

        chosen = None

        # Walk forward only a bounded distance until a useful,
        # recallable text document with a queryable title appears.
        for _ in range(250):

            row = connection.execute(
                """
                SELECT
                    rd.id,
                    rd.title,
                    rd.file_path,
                    rd.media_type,
                    rd.content_chars
                FROM runtime_documents rd
                WHERE rd.id >= ?
                  AND rd.content_chars >= 500
                  AND EXISTS (
                      SELECT 1
                      FROM runtime_chunks rc
                      WHERE rc.document_id = rd.id
                  )
                ORDER BY rd.id
                LIMIT 1
                """,
                (cursor,),
            ).fetchone()

            if row is None:
                break

            data = dict(row)

            query = title_query(
                str(
                    data["title"]
                )
            )

            normalized_title = (
                str(
                    data["title"]
                )
                .strip()
                .casefold()
            )

            if (
                query
                and int(data["id"])
                not in seen_ids
                and normalized_title
                not in seen_titles
            ):

                data[
                    "benchmark_query"
                ] = query

                chosen = data

                break

            cursor = (
                int(
                    data["id"]
                )
                + 1
            )

        if chosen is None:
            continue

        seen_ids.add(
            int(
                chosen["id"]
            )
        )

        seen_titles.add(
            str(
                chosen["title"]
            )
            .strip()
            .casefold()
        )

        sample.append(
            chosen
        )

    return sample


# ============================================================
# BENCHMARK ONE QUERY
# ============================================================

def benchmark_query(
    *,
    query: str,
    expected: dict[str, Any],
    db_path: Path,
    search_catalog: Any,
    search_qualified_catalog: Any,
    qualify_rows: Any,
    engine: Any,
    rescue_fn: Any,
    limit: int = 25,
) -> dict[str, Any]:

    raw = list(
        search_catalog(
            query,
            db_path=db_path,
            limit=limit,
        )
    )

    qualified = list(
        search_qualified_catalog(
            query,
            db_path=db_path,
            limit=limit,
            engine=engine,
        )
    )

    runtime_id = int(
        expected["id"]
    )

    path = str(
        expected["file_path"]
    )

    raw_rank = rank_expected(
        raw,
        runtime_id=runtime_id,
        expected_path=path,
    )

    qualified_rank = rank_expected(
        qualified,
        runtime_id=runtime_id,
        expected_path=path,
    )

    qualified_row = expected_result(
        qualified,
        runtime_id=runtime_id,
        expected_path=path,
    )

    diagnosis = None

    if raw_rank is None:

        status = (
            "RAW_RETRIEVAL_MISS"
        )

    elif qualified_rank is None:

        status = (
            "QUALIFICATION_DROP"
        )

        diagnosis = (
            qualification_diagnosis(
                query=query,
                raw_rows=raw,
                expected_path=path,
                engine=engine,
                qualify_rows=
                    qualify_rows,
                rescue_fn=
                    rescue_fn,
            )
        )

    else:

        status = (
            "QUALIFIED_RECALL_PASS"
        )

    return {
        "query":
            query,

        "runtime_id":
            runtime_id,

        "title":
            expected["title"],

        "file_path":
            path,

        "raw_count":
            len(raw),

        "qualified_count":
            len(qualified),

        "raw_rank":
            raw_rank,

        "qualified_rank":
            qualified_rank,

        "status":
            status,

        "qualification_decision":
            (
                qualified_row.get(
                    "qualification_decision"
                )
                if qualified_row
                else None
            ),

        "qualification_rescue":
            (
                qualified_row.get(
                    "qualification_rescue"
                )
                if qualified_row
                else None
            ),

        "qualification_rescue_reason":
            (
                qualified_row.get(
                    "qualification_rescue_reason"
                )
                if qualified_row
                else None
            ),

        "drop_diagnosis":
            diagnosis,
    }


# ============================================================
# METRICS
# ============================================================

def recall_at(
    results: list[dict[str, Any]],
    field: str,
    k: int,
) -> int:

    return sum(
        1
        for item in results
        if (
            item.get(field)
            is not None
            and int(
                item[field]
            )
            <= k
        )
    )


def percent(
    numerator: int,
    denominator: int,
) -> float:

    if denominator == 0:
        return 0.0

    return (
        numerator
        * 100.0
        / denominator
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
        "--sample-size",
        type=int,
        default=100,
    )

    args = parser.parse_args()

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

    engine = QualificationEngine()

    connection = ro(
        args.db
    )


    try:

        print(
            "============================================================"
        )

        print(
            " GENESIS RECALL R1F-R4"
        )

        print(
            " PRODUCTION RECALL REGRESSION + CORPUS BENCHMARK"
        )

        print(
            "============================================================"
        )


        # ====================================================
        # 1. KNOWN SEMANTIC REGRESSION
        # ====================================================

        print()
        print(
            "=== 1. KNOWN SEMANTIC CANARIES ==="
        )

        known_results = []

        for spec in KNOWN:

            expected = runtime_document(
                connection,
                spec["runtime_id"],
            )

            if expected is None:

                result = {
                    **spec,
                    "status":
                        "EXPECTED_RUNTIME_DOCUMENT_MISSING",
                    "raw_rank":
                        None,
                    "qualified_rank":
                        None,
                }

                known_results.append(
                    result
                )

                print()
                print(
                    spec["name"],
                    ": EXPECTED RUNTIME DOCUMENT MISSING",
                )

                continue


            result = benchmark_query(
                query=spec["query"],
                expected=expected,
                db_path=args.db,
                search_catalog=
                    search_catalog,
                search_qualified_catalog=
                    search_qualified_catalog,
                qualify_rows=
                    qualify_rows,
                engine=engine,
                rescue_fn=
                    _gate_repair_should_rescue,
            )

            result.update(
                {
                    "name":
                        spec["name"],
                    "expect_r1f":
                        spec[
                            "expect_r1f"
                        ],
                }
            )

            known_results.append(
                result
            )

            print()
            print(
                spec["name"],
            )

            print(
                "  query          :",
                spec["query"],
            )

            print(
                "  raw rank       :",
                result[
                    "raw_rank"
                ],
            )

            print(
                "  qualified rank :",
                result[
                    "qualified_rank"
                ],
            )

            print(
                "  decision       :",
                result[
                    "qualification_decision"
                ],
            )

            print(
                "  rescue reason  :",
                result[
                    "qualification_rescue_reason"
                ],
            )

            print(
                "  status         :",
                result[
                    "status"
                ],
            )


        known_total = len(
            known_results
        )

        known_raw5 = recall_at(
            known_results,
            "raw_rank",
            5,
        )

        known_qualified5 = recall_at(
            known_results,
            "qualified_rank",
            5,
        )

        python_result = next(
            (
                item
                for item in known_results
                if item.get("name")
                == "ai_assisted_python"
            ),
            None,
        )

        python_r1f_pass = bool(
            python_result
            and python_result.get(
                "qualified_rank"
            )
            is not None
            and int(
                python_result[
                    "qualified_rank"
                ]
            )
            <= 5
            and python_result.get(
                "qualification_rescue_reason"
            )
            == R1F_REASON
        )


        # ====================================================
        # 2. STRATIFIED 100-DOCUMENT CATALOG RECALL SAMPLE
        # ====================================================

        print()
        print(
            "=== 2. STRATIFIED CORPUS SAMPLE ==="
        )

        sample = choose_sample(
            connection,
            args.sample_size,
        )

        print(
            "requested sample :",
            args.sample_size,
        )

        print(
            "selected sample  :",
            len(sample),
        )

        corpus_results = []

        for index, expected in enumerate(
            sample,
            start=1,
        ):

            result = benchmark_query(
                query=expected[
                    "benchmark_query"
                ],
                expected=expected,
                db_path=args.db,
                search_catalog=
                    search_catalog,
                search_qualified_catalog=
                    search_qualified_catalog,
                qualify_rows=
                    qualify_rows,
                engine=engine,
                rescue_fn=
                    _gate_repair_should_rescue,
            )

            corpus_results.append(
                result
            )

            print(
                f"[{index:03d}/{len(sample):03d}] "
                f"id={expected['id']:<7} "
                f"raw={str(result['raw_rank']):<4} "
                f"qualified={str(result['qualified_rank']):<4} "
                f"{result['status']}"
            )

            print(
                "      query:",
                expected[
                    "benchmark_query"
                ],
            )

            if (
                result[
                    "status"
                ]
                == "QUALIFICATION_DROP"
            ):

                diag = (
                    result.get(
                        "drop_diagnosis"
                    )
                    or {}
                )

                print(
                    "      DROP:",
                    diag.get(
                        "decision"
                    ),
                    diag.get(
                        "explanation"
                    ),
                )

                print(
                    "      rescue:",
                    diag.get(
                        "rescue"
                    ),
                    diag.get(
                        "rescue_reason"
                    ),
                )


        corpus_total = len(
            corpus_results
        )

        raw1 = recall_at(
            corpus_results,
            "raw_rank",
            1,
        )

        raw5 = recall_at(
            corpus_results,
            "raw_rank",
            5,
        )

        raw20 = recall_at(
            corpus_results,
            "raw_rank",
            20,
        )

        qual1 = recall_at(
            corpus_results,
            "qualified_rank",
            1,
        )

        qual5 = recall_at(
            corpus_results,
            "qualified_rank",
            5,
        )

        qual20 = recall_at(
            corpus_results,
            "qualified_rank",
            20,
        )


        # ====================================================
        # 3. QUALIFICATION LOSS ANALYSIS
        # ====================================================

        print()
        print(
            "=== 3. QUALIFICATION LOSS ANALYSIS ==="
        )

        drops = [
            item
            for item in corpus_results
            if item[
                "status"
            ]
            == "QUALIFICATION_DROP"
        ]

        drop_reasons = Counter()

        for item in drops:

            diagnosis = (
                item.get(
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
            "raw-hit / qualified-drop :",
            len(drops),
        )

        for reason, count in (
            drop_reasons.most_common()
        ):

            print(
                f"  {reason:36} : {count}"
            )


        # ====================================================
        # 4. R1F RESCUE USAGE
        # ====================================================

        print()
        print(
            "=== 4. R1F RESCUE USAGE ==="
        )

        corpus_r1f = [
            item
            for item in corpus_results
            if item.get(
                "qualification_rescue_reason"
            )
            == R1F_REASON
        ]

        known_r1f = [
            item
            for item in known_results
            if item.get(
                "qualification_rescue_reason"
            )
            == R1F_REASON
        ]

        print(
            "known R1F rescues  :",
            len(known_r1f),
        )

        print(
            "corpus R1F rescues :",
            len(corpus_r1f),
        )

        for item in corpus_r1f[:20]:

            print(
                "  id=",
                item["runtime_id"],
                " rank=",
                item["qualified_rank"],
                " ",
                item["title"],
                sep="",
            )


        # ====================================================
        # 5. ADVERSARIAL CONTROLS
        # ====================================================

        print()
        print(
            "=== 5. ADVERSARIAL CONTROLS ==="
        )

        negative_results = []

        false_r1f_rescues = 0

        for query in NEGATIVE:

            qualified = list(
                search_qualified_catalog(
                    query,
                    db_path=args.db,
                    limit=25,
                    engine=engine,
                )
            )

            r1f_rows = [
                row
                for row in qualified
                if row.get(
                    "qualification_rescue_reason"
                )
                == R1F_REASON
            ]

            false_r1f_rescues += (
                len(r1f_rows)
            )

            record = {
                "query":
                    query,

                "qualified_count":
                    len(qualified),

                "r1f_rescue_count":
                    len(r1f_rows),

                "r1f_results": [
                    {
                        "document_id":
                            result_runtime_id(
                                row
                            ),

                        "title":
                            row.get(
                                "title"
                            ),

                        "file_path":
                            result_path(
                                row
                            ),
                    }
                    for row
                    in r1f_rows[:10]
                ],
            }

            negative_results.append(
                record
            )

            print()
            print(
                "query:",
                query,
            )

            print(
                "  qualified results :",
                len(qualified),
            )

            print(
                "  R1F rescues       :",
                len(r1f_rows),
            )


        # ====================================================
        # 6. QUALITY GRADE
        #
        # First benchmark establishes baseline; these grades are
        # descriptive, not mutation/rollback gates.
        # ====================================================

        qualified5_pct = percent(
            qual5,
            corpus_total,
        )

        if qualified5_pct >= 95.0:

            corpus_grade = (
                "EXCELLENT"
            )

        elif qualified5_pct >= 90.0:

            corpus_grade = (
                "STRONG"
            )

        elif qualified5_pct >= 80.0:

            corpus_grade = (
                "NEEDS_IMPROVEMENT"
            )

        else:

            corpus_grade = (
                "RECALL_DEFICIENT"
            )


        # ====================================================
        # 7. CERTIFICATION GATES
        #
        # We do NOT use the first corpus sample as a hard
        # threshold because R1F-R4 establishes the baseline.
        #
        # Hard regression conditions:
        #
        #  - all known canaries top-5
        #  - Python uses the R1F rescue path
        #  - zero adversarial R1F rescues
        # ====================================================

        known_regression_pass = (
            known_qualified5
            == known_total
        )

        adversarial_pass = (
            false_r1f_rescues
            == 0
        )

        regression_certified = (
            known_regression_pass
            and python_r1f_pass
            and adversarial_pass
        )


        elapsed = (
            time.monotonic()
            - started
        )


        # ====================================================
        # 8. SUMMARY
        # ====================================================

        print()
        print(
            "============================================================"
        )

        print(
            " JARVIS PRODUCTION RECALL BENCHMARK"
        )

        print(
            "============================================================"
        )

        print()
        print(
            "KNOWN SEMANTIC CANARIES"
        )

        print(
            f"  tested                 : {known_total}"
        )

        print(
            f"  raw recall @5          : "
            f"{known_raw5}/{known_total} "
            f"({percent(known_raw5, known_total):.1f}%)"
        )

        print(
            f"  qualified recall @5    : "
            f"{known_qualified5}/{known_total} "
            f"({percent(known_qualified5, known_total):.1f}%)"
        )

        print(
            f"  Python R1F rescue      : "
            f"{'PASS' if python_r1f_pass else 'FAIL'}"
        )


        print()
        print(
            "STRATIFIED CATALOG RECALL"
        )

        print(
            f"  sampled documents      : {corpus_total}"
        )

        print(
            f"  raw recall @1          : "
            f"{raw1}/{corpus_total} "
            f"({percent(raw1, corpus_total):.1f}%)"
        )

        print(
            f"  raw recall @5          : "
            f"{raw5}/{corpus_total} "
            f"({percent(raw5, corpus_total):.1f}%)"
        )

        print(
            f"  raw recall @20         : "
            f"{raw20}/{corpus_total} "
            f"({percent(raw20, corpus_total):.1f}%)"
        )

        print(
            f"  qualified recall @1    : "
            f"{qual1}/{corpus_total} "
            f"({percent(qual1, corpus_total):.1f}%)"
        )

        print(
            f"  qualified recall @5    : "
            f"{qual5}/{corpus_total} "
            f"({percent(qual5, corpus_total):.1f}%)"
        )

        print(
            f"  qualified recall @20   : "
            f"{qual20}/{corpus_total} "
            f"({percent(qual20, corpus_total):.1f}%)"
        )

        print(
            f"  qualification drops    : {len(drops)}"
        )

        print(
            f"  R1F corpus rescues     : {len(corpus_r1f)}"
        )

        print(
            f"  corpus recall grade    : {corpus_grade}"
        )


        print()
        print(
            "ADVERSARIAL CONTROLS"
        )

        print(
            f"  queries                : {len(NEGATIVE)}"
        )

        print(
            f"  false R1F rescues      : {false_r1f_rescues}"
        )

        print(
            f"  adversarial gate       : "
            f"{'PASS' if adversarial_pass else 'FAIL'}"
        )


        print()
        print(
            "REGRESSION CERTIFICATION"
        )

        print(
            f"  known regression       : "
            f"{'PASS' if known_regression_pass else 'FAIL'}"
        )

        print(
            f"  Python repair          : "
            f"{'PASS' if python_r1f_pass else 'FAIL'}"
        )

        print(
            f"  adversarial precision  : "
            f"{'PASS' if adversarial_pass else 'FAIL'}"
        )

        print(
            f"  R1F-R4 CERTIFIED       : "
            f"{regression_certified}"
        )

        print()
        print(
            f"elapsed seconds          : {elapsed:.2f}"
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


        report = {
            "schema":
                "genesis-recall-r1f-r4-v1",

            "read_only":
                True,

            "known_semantic": {
                "results":
                    known_results,

                "tested":
                    known_total,

                "raw_recall_at_5":
                    known_raw5,

                "qualified_recall_at_5":
                    known_qualified5,

                "python_r1f_pass":
                    python_r1f_pass,
            },

            "corpus_sample": {
                "requested":
                    args.sample_size,

                "selected":
                    corpus_total,

                "results":
                    corpus_results,

                "raw_recall_at_1":
                    raw1,

                "raw_recall_at_5":
                    raw5,

                "raw_recall_at_20":
                    raw20,

                "qualified_recall_at_1":
                    qual1,

                "qualified_recall_at_5":
                    qual5,

                "qualified_recall_at_20":
                    qual20,

                "qualification_drops":
                    len(drops),

                "drop_reasons":
                    dict(
                        drop_reasons
                    ),

                "r1f_rescues":
                    len(corpus_r1f),

                "grade":
                    corpus_grade,
            },

            "adversarial": {
                "queries":
                    negative_results,

                "false_r1f_rescues":
                    false_r1f_rescues,

                "pass":
                    adversarial_pass,
            },

            "certification": {
                "known_regression_pass":
                    known_regression_pass,

                "python_r1f_pass":
                    python_r1f_pass,

                "adversarial_pass":
                    adversarial_pass,

                "certified":
                    regression_certified,
            },

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


        print()
        print(
            "JSON report:",
            args.report,
        )


        return (
            0
            if regression_certified
            else 1
        )


    finally:

        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
