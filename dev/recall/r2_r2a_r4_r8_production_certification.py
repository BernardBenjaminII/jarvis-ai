from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

REPORT = Path(
    sys.argv[1]
)


import core.knowledge_catalog.qualified_search as qs

from core.knowledge_catalog.search import (
    search_catalog,
)

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


# ============================================================
# IDENTITY HELPERS FOR CERTIFICATION
# ============================================================

def ordinary_row_document_id(
    row: Any,
) -> int | None:

    for name in (
        "document_id",
        "runtime_document_id",
        "id",
    ):

        try:
            if isinstance(row, dict):
                value = row.get(name)
            else:
                value = getattr(
                    row,
                    name,
                    None,
                )
        except Exception:
            value = None

        if value is None:
            continue

        try:
            return int(value)
        except Exception:
            continue

    return None


def rank_of(
    rows: list[Any],
    target: int,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):
        if (
            ordinary_row_document_id(row)
            == target
        ):
            return rank

    return None


# ============================================================
# LIVE R1F/R2 INSTRUMENTATION
#
# Patch the exact globals used by search_qualified_catalog.
# Process-local only.
# ============================================================

fn_globals = (
    qs.search_qualified_catalog.__globals__
)

REAL_R1F = fn_globals[
    "_gate_repair_should_rescue"
]

REAL_R2 = fn_globals[
    "_r2_exact_document_identity_should_rescue"
]


r1f_events: list[dict[str, Any]] = []
r2_events: list[dict[str, Any]] = []


def traced_r1f(
    query: str,
    evidence: Any,
    *,
    threshold: float,
):

    result = REAL_R1F(
        query,
        evidence,
        threshold=threshold,
    )

    document_id = (
        qs._r2_evidence_document_id(
            evidence
        )
    )

    chunk_id = (
        qs._r2_evidence_chunk_id(
            evidence
        )
    )

    r1f_events.append(
        {
            "query": query,
            "document_id": document_id,
            "chunk_id": chunk_id,
            "result": list(result),
        }
    )

    return result


def traced_r2(
    query: str,
    evidence: Any,
    *,
    target_document_ids: frozenset[int],
):

    result = REAL_R2(
        query,
        evidence,
        target_document_ids=target_document_ids,
    )

    document_id = (
        qs._r2_evidence_document_id(
            evidence
        )
    )

    chunk_id = (
        qs._r2_evidence_chunk_id(
            evidence
        )
    )

    r2_events.append(
        {
            "query": query,
            "document_id": document_id,
            "chunk_id": chunk_id,
            "target_document_ids": sorted(
                target_document_ids
            ),
            "rescue": bool(
                result[0]
            ),
            "reason": result[1],
        }
    )

    return result


fn_globals[
    "_gate_repair_should_rescue"
] = traced_r1f

fn_globals[
    "_r2_exact_document_identity_should_rescue"
] = traced_r2


report: dict[str, Any] = {
    "known_canaries": [],
    "semantic_regression": [],
    "adversarial": [],
    "near_miss": [],
}


all_pass = True


try:

    # ========================================================
    # A. LANE EXACT DOCUMENT RESCUE
    # ========================================================

    print()
    print("=" * 76)
    print(" A. LANE EXACT DOCUMENT IDENTITY RESCUE")
    print("=" * 76)

    LANE_QUERY = (
        "Edward William Lane Arabic English "
        "Lexicon Vol 6"
    )

    LANE_ID = 86876

    r1f_start = len(r1f_events)
    r2_start = len(r2_events)

    raw = search_catalog(
        LANE_QUERY,
        db_path=DB,
        limit=100,
    )

    qualified = (
        qs.search_qualified_catalog(
            LANE_QUERY,
            db_path=DB,
            limit=100,
        )
    )

    raw_rank = rank_of(
        raw,
        LANE_ID,
    )

    qualified_rank = rank_of(
        qualified,
        LANE_ID,
    )

    lane_r1f = [
        event
        for event
        in r1f_events[
            r1f_start:
        ]
        if event[
            "document_id"
        ] == LANE_ID
    ]

    lane_r2 = [
        event
        for event
        in r2_events[
            r2_start:
        ]
        if event[
            "document_id"
        ] == LANE_ID
    ]

    lane_r2_success = any(
        event["rescue"] is True
        and event["reason"]
        == "exact_unique_document_identity"
        and event["target_document_ids"]
        == [LANE_ID]
        for event in lane_r2
    )

    print("raw rank            :", raw_rank)
    print("qualified rank      :", qualified_rank)
    print("Lane R1F events     :", len(lane_r1f))
    print("Lane R2 events      :", len(lane_r2))
    print("Lane exact R2 rescue:", lane_r2_success)

    if lane_r2:

        print()
        print("First Lane R2 event:")

        for key, value in lane_r2[0].items():
            print(
                f"  {key:<22}: {value}"
            )

    lane_pass = (
        raw_rank is not None
        and raw_rank <= 5
        and qualified_rank is not None
        and qualified_rank <= 5
        and lane_r2_success
    )

    print(
        "LANE EXACT IDENTITY GATE:",
        "PASS"
        if lane_pass
        else "FAIL",
    )

    all_pass = (
        all_pass
        and lane_pass
    )


    # ========================================================
    # B. REGRESSION CANARIES
    # ========================================================

    print()
    print("=" * 76)
    print(" B. KNOWN PRODUCTION CANARIES")
    print("=" * 76)

    canaries = (
        (
            "ai_assisted_python",
            "AI assisted Python programming",
            11,
        ),
        (
            "cpp",
            "C++ programming",
            4,
        ),
        (
            "effective_c",
            "effective C programming",
            14,
        ),
    )


    for name, query, target in canaries:

        raw_rows = search_catalog(
            query,
            db_path=DB,
            limit=100,
        )

        qualified_rows = (
            qs.search_qualified_catalog(
                query,
                db_path=DB,
                limit=100,
            )
        )

        rr = rank_of(
            raw_rows,
            target,
        )

        qr = rank_of(
            qualified_rows,
            target,
        )

        passed = (
            rr is not None
            and rr <= 5
            and qr is not None
            and qr <= 5
        )

        print()
        print(name)
        print("  target ID      :", target)
        print("  raw rank       :", rr)
        print("  qualified rank :", qr)
        print("  PASS           :", passed)

        report[
            "known_canaries"
        ].append(
            {
                "name": name,
                "target_id": target,
                "raw_rank": rr,
                "qualified_rank": qr,
                "pass": passed,
            }
        )

        all_pass = (
            all_pass
            and passed
        )


    # ========================================================
    # C. VERIFY PYTHON R1F STILL OPERATES
    # ========================================================

    print()
    print("=" * 76)
    print(" C. R1F CONTENT RESCUE PRESERVATION")
    print("=" * 76)

    python_r1f = [
        event
        for event in r1f_events
        if (
            event["query"]
            == "AI assisted Python programming"
            and event["document_id"] == 11
            and event["result"][0] is True
        )
    ]

    r1f_preserved = (
        len(python_r1f) > 0
    )

    print(
        "Python successful R1F events:",
        len(python_r1f),
    )

    if python_r1f:
        print(
            "reason:",
            python_r1f[0][
                "result"
            ][1],
        )

    print(
        "R1F PRESERVED:",
        r1f_preserved,
    )

    all_pass = (
        all_pass
        and r1f_preserved
    )


    # ========================================================
    # D. SEMANTIC REGRESSION
    # ========================================================

    print()
    print("=" * 76)
    print(" D. SEMANTIC REGRESSION")
    print("=" * 76)

    semantic_queries = (
        "civil defense manual",
        "US Army survival manual",
        "practical electronics handbook",
        "Marx mathematical manuscripts",
    )


    for query in semantic_queries:

        raw_rows = search_catalog(
            query,
            db_path=DB,
            limit=20,
        )

        qualified_rows = (
            qs.search_qualified_catalog(
                query,
                db_path=DB,
                limit=20,
            )
        )

        passed = (
            bool(raw_rows)
            and bool(qualified_rows)
        )

        print()
        print(query)
        print(
            "  raw       :",
            len(raw_rows),
        )
        print(
            "  qualified :",
            len(qualified_rows),
        )
        print(
            "  PASS      :",
            passed,
        )

        report[
            "semantic_regression"
        ].append(
            {
                "query": query,
                "raw": len(raw_rows),
                "qualified": len(
                    qualified_rows
                ),
                "pass": passed,
            }
        )

        all_pass = (
            all_pass
            and passed
        )


    # ========================================================
    # E. ADVERSARIAL PRECISION
    # ========================================================

    print()
    print("=" * 76)
    print(" E. ADVERSARIAL PRECISION")
    print("=" * 76)

    adversarial_queries = (
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


    for query in adversarial_queries:

        start = len(r2_events)

        qualified_rows = (
            qs.search_qualified_catalog(
                query,
                db_path=DB,
                limit=25,
            )
        )

        new_r2 = r2_events[
            start:
        ]

        successful_r2 = [
            event
            for event in new_r2
            if event["rescue"] is True
        ]

        passed = (
            len(qualified_rows) == 0
            and len(
                successful_r2
            ) == 0
        )

        print()
        print(query)
        print(
            "  qualified  :",
            len(qualified_rows),
        )
        print(
            "  R2 rescues :",
            len(successful_r2),
        )
        print(
            "  PASS       :",
            passed,
        )

        report[
            "adversarial"
        ].append(
            {
                "query": query,
                "qualified": len(
                    qualified_rows
                ),
                "r2_rescues": len(
                    successful_r2
                ),
                "pass": passed,
            }
        )

        all_pass = (
            all_pass
            and passed
        )


    # ========================================================
    # F. NEIGHBORING VOLUME PRECISION
    # ========================================================

    print()
    print("=" * 76)
    print(" F. LANE DOCUMENT-ID PRECISION")
    print("=" * 76)

    # Wrong-volume query may legitimately identify and rescue
    # the ACTUAL Vol.5 document. The requirement is simply that
    # document 86876 (Vol.6) must not be rescued for it.

    near_misses = (
        (
            "wrong_volume",
            (
                "Edward William Lane Arabic English "
                "Lexicon Vol 5"
            ),
        ),
        (
            "wrong_author",
            (
                "Richard William Lane Arabic English "
                "Lexicon Vol 6"
            ),
        ),
        (
            "wrong_work",
            (
                "Edward William Lane Arabic English "
                "Grammar Vol 6"
            ),
        ),
        (
            "extra_identity_term",
            (
                "Edward William Lane Arabic English "
                "Lexicon Vol 6 Supplement"
            ),
        ),
    )


    for name, query in near_misses:

        start = len(r2_events)

        qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=100,
        )

        events = r2_events[
            start:
        ]

        lane_rescued = any(
            event["document_id"]
            == LANE_ID
            and event["rescue"] is True
            for event in events
        )

        passed = (
            not lane_rescued
        )

        print()
        print(name)
        print(
            "  query            :",
            query,
        )
        print(
            "  Lane 86876 rescue:",
            lane_rescued,
        )
        print(
            "  PASS             :",
            passed,
        )

        report[
            "near_miss"
        ].append(
            {
                "name": name,
                "query": query,
                "lane_86876_rescued":
                    lane_rescued,
                "pass": passed,
            }
        )

        all_pass = (
            all_pass
            and passed
        )


    # ========================================================
    # G. AMBIGUOUS MULTI-VOLUME QUERY
    # ========================================================

    print()
    print("=" * 76)
    print(" G. AMBIGUOUS IDENTITY BOUNDARY")
    print("=" * 76)

    ambiguous_query = (
        "Edward William Lane Arabic English Lexicon"
    )

    start = len(r2_events)

    qs.search_qualified_catalog(
        ambiguous_query,
        db_path=DB,
        limit=100,
    )

    ambiguous_events = r2_events[
        start:
    ]

    ambiguous_successes = [
        event
        for event in ambiguous_events
        if event["rescue"] is True
    ]

    ambiguous_pass = (
        len(
            ambiguous_successes
        )
        == 0
    )

    print(
        "query:",
        ambiguous_query,
    )
    print(
        "successful R2 rescues:",
        len(
            ambiguous_successes
        ),
    )
    print(
        "PASS:",
        ambiguous_pass,
    )

    all_pass = (
        all_pass
        and ambiguous_pass
    )


    # ========================================================
    # H. SHORT QUERY BOUNDARY
    # ========================================================

    print()
    print("=" * 76)
    print(" H. SHORT IDENTITY QUERY BOUNDARY")
    print("=" * 76)

    short_queries = (
        "Lane Lexicon",
        "Arabic Lexicon",
        "English Dictionary",
    )

    short_pass = True

    for query in short_queries:

        start = len(r2_events)

        qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=50,
        )

        events = r2_events[
            start:
        ]

        successes = [
            event
            for event in events
            if event["rescue"] is True
        ]

        passed = (
            len(successes) == 0
        )

        short_pass = (
            short_pass
            and passed
        )

        print()
        print(query)
        print(
            "  R2 rescues:",
            len(successes),
        )
        print(
            "  PASS      :",
            passed,
        )

    all_pass = (
        all_pass
        and short_pass
    )


    # ========================================================
    # I. THRESHOLDS
    # ========================================================

    print()
    print("=" * 76)
    print(" I. THRESHOLD IMMUTABILITY")
    print("=" * 76)

    engine = QualificationEngine()

    thresholds_pass = (
        engine.thresholds.accept
        == 0.35
        and
        engine.thresholds.minimum_confidence
        == 0.05
        and
        engine.thresholds.minimum_lexical
        == 0.2
        and
        engine.thresholds.minimum_subject
        == 0.1
        and
        engine.thresholds.minimum_phrase
        == 0.0
    )

    print(
        "accept             :",
        engine.thresholds.accept,
    )
    print(
        "minimum_confidence :",
        engine.thresholds.minimum_confidence,
    )
    print(
        "minimum_lexical    :",
        engine.thresholds.minimum_lexical,
    )
    print(
        "minimum_subject    :",
        engine.thresholds.minimum_subject,
    )

    print(
        "PASS:",
        thresholds_pass,
    )

    all_pass = (
        all_pass
        and thresholds_pass
    )


finally:

    fn_globals[
        "_gate_repair_should_rescue"
    ] = REAL_R1F

    fn_globals[
        "_r2_exact_document_identity_should_rescue"
    ] = REAL_R2


# ============================================================
# J. SUMMARY
# ============================================================

r2_successes = [
    event
    for event in r2_events
    if event["rescue"] is True
]


report[
    "lane"
] = {
    "target_document_id":
        LANE_ID,

    "raw_rank":
        raw_rank,

    "qualified_rank":
        qualified_rank,

    "r1f_events":
        lane_r1f,

    "r2_events":
        lane_r2,

    "r2_exact_rescue":
        lane_r2_success,

    "pass":
        lane_pass,
}


report[
    "summary"
] = {
    "lane_exact_identity_pass":
        lane_pass,

    "lane_r2_exact_rescue":
        lane_r2_success,

    "known_canaries_pass":
        all(
            item["pass"]
            for item
            in report[
                "known_canaries"
            ]
        ),

    "r1f_preserved":
        r1f_preserved,

    "semantic_regression_pass":
        all(
            item["pass"]
            for item
            in report[
                "semantic_regression"
            ]
        ),

    "adversarial_precision_pass":
        all(
            item["pass"]
            for item
            in report[
                "adversarial"
            ]
        ),

    "near_miss_precision_pass":
        all(
            item["pass"]
            for item
            in report[
                "near_miss"
            ]
        ),

    "ambiguous_identity_pass":
        ambiguous_pass,

    "short_query_boundary_pass":
        short_pass,

    "thresholds_unchanged":
        thresholds_pass,

    "r2_calls":
        len(r2_events),

    "r2_successes":
        len(r2_successes),

    "certified":
        all_pass,
}


REPORT.write_text(
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
print("=" * 76)
print(" GENESIS RECALL R2-R2A-R4-R8 RESULT")
print("=" * 76)

summary = report[
    "summary"
]

for key in (
    "lane_exact_identity_pass",
    "lane_r2_exact_rescue",
    "known_canaries_pass",
    "r1f_preserved",
    "semantic_regression_pass",
    "adversarial_precision_pass",
    "near_miss_precision_pass",
    "ambiguous_identity_pass",
    "short_query_boundary_pass",
    "thresholds_unchanged",
):
    print(
        f"{key:<32}:",
        summary[key],
    )

print()
print(
    "R2 calls                     :",
    summary["r2_calls"],
)

print(
    "R2 successful rescues        :",
    summary["r2_successes"],
)

print()
print(
    "R2-R2A-R4-R8 CERTIFIED       :",
    all_pass,
)

print("=" * 76)

raise SystemExit(
    0 if all_pass else 1
)
