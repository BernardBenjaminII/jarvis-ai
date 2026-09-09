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
# Utilities
# ============================================================

def value_from(
    obj: Any,
    key: str,
) -> Any:

    if isinstance(
        obj,
        dict,
    ):
        return obj.get(key)

    try:
        return getattr(
            obj,
            key,
            None,
        )
    except Exception:
        return None


def document_id(
    obj: Any,
) -> int | None:

    for key in (
        "runtime_document_id",
        "document_id",
        "id",
    ):

        value = value_from(
            obj,
            key,
        )

        if value is None:
            continue

        try:
            return int(value)
        except Exception:
            continue

    return None


def candidate_from_evidence(
    evidence: Any,
) -> Any:

    try:
        return evidence.candidate
    except Exception:
        return None


def rank_of(
    rows: list[Any],
    target_id: int,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        if (
            document_id(row)
            == target_id
        ):
            return rank

    return None


def safe_score(
    evidence: Any,
    field: str,
) -> float | None:

    try:
        score = evidence.score
        value = getattr(
            score,
            field,
        )
        return float(value)
    except Exception:
        return None


# ============================================================
# Live instrumentation
# ============================================================

REAL_R2 = (
    qs._r2_identity_should_rescue
)

REAL_R1F = (
    qs._gate_repair_should_rescue
)

r2_events: list[dict[str, Any]] = []
r1f_events: list[dict[str, Any]] = []


def traced_r2(
    query: str,
    evidence: Any,
):

    rescue, reason = REAL_R2(
        query,
        evidence,
    )

    candidate = (
        candidate_from_evidence(
            evidence
        )
    )

    event = {
        "query":
            query,

        "document_id":
            document_id(
                candidate
            ),

        "title":
            value_from(
                candidate,
                "title",
            ),

        "subject":
            value_from(
                candidate,
                "subject",
            ),

        "source_path":
            value_from(
                candidate,
                "source_path",
            ),

        "lexical":
            safe_score(
                evidence,
                "lexical",
            ),

        "entity":
            safe_score(
                evidence,
                "entity",
            ),

        "subject_score":
            safe_score(
                evidence,
                "subject",
            ),

        "provenance":
            safe_score(
                evidence,
                "provenance",
            ),

        "final":
            safe_score(
                evidence,
                "final",
            ),

        "rescue":
            bool(rescue),

        "reason":
            reason,
    }

    r2_events.append(
        event
    )

    return rescue, reason


def traced_r1f(
    query: str,
    evidence: Any,
    *,
    threshold: float,
):

    rescue, reason = REAL_R1F(
        query,
        evidence,
        threshold=threshold,
    )

    candidate = (
        candidate_from_evidence(
            evidence
        )
    )

    r1f_events.append(
        {
            "query":
                query,

            "document_id":
                document_id(
                    candidate
                ),

            "title":
                value_from(
                    candidate,
                    "title",
                ),

            "rescue":
                bool(rescue),

            "reason":
                reason,
        }
    )

    return rescue, reason


# Monkey-patching is process-local.
#
# No source files are modified here.
qs._r2_identity_should_rescue = traced_r2
qs._gate_repair_should_rescue = traced_r1f


report: dict[str, Any] = {
    "production_canaries": [],
    "semantic_regression": [],
    "adversarial": [],
    "near_miss": [],
    "r2_events": r2_events,
    "r1f_events": r1f_events,
}


all_pass = True


# ============================================================
# A. LIVE LANE PRODUCTION PATH
# ============================================================

print()
print("=" * 76)
print(" A. LIVE LANE PRODUCTION PATH")
print("=" * 76)

LANE_QUERY = (
    "Edward William Lane Arabic English "
    "Lexicon Vol 6"
)

LANE_ID = 86876


lane_raw = search_catalog(
    LANE_QUERY,
    db_path=DB,
    limit=100,
)

r2_start = len(
    r2_events
)

r1f_start = len(
    r1f_events
)

lane_qualified = (
    qs.search_qualified_catalog(
        LANE_QUERY,
        db_path=DB,
        limit=100,
    )
)

lane_raw_rank = rank_of(
    lane_raw,
    LANE_ID,
)

lane_qualified_rank = rank_of(
    lane_qualified,
    LANE_ID,
)

lane_r2_events = [
    event
    for event
    in r2_events[
        r2_start:
    ]
    if (
        event[
            "document_id"
        ]
        == LANE_ID
    )
]

lane_r1f_events = [
    event
    for event
    in r1f_events[
        r1f_start:
    ]
    if (
        event[
            "document_id"
        ]
        == LANE_ID
    )
]


print(
    "raw rank       :",
    lane_raw_rank,
)

print(
    "qualified rank :",
    lane_qualified_rank,
)

print(
    "Lane R1F events:",
    len(
        lane_r1f_events
    ),
)

print(
    "Lane R2 events :",
    len(
        lane_r2_events
    ),
)


for event in lane_r1f_events:

    print()
    print(
        "R1F EVENT"
    )

    print(
        "  rescue :",
        event[
            "rescue"
        ],
    )

    print(
        "  reason :",
        event[
            "reason"
        ],
    )


for event in lane_r2_events:

    print()
    print(
        "R2 EVENT"
    )

    print(
        "  title      :",
        event[
            "title"
        ],
    )

    print(
        "  lexical    :",
        event[
            "lexical"
        ],
    )

    print(
        "  entity     :",
        event[
            "entity"
        ],
    )

    print(
        "  subject    :",
        event[
            "subject_score"
        ],
    )

    print(
        "  provenance :",
        event[
            "provenance"
        ],
    )

    print(
        "  final      :",
        event[
            "final"
        ],
    )

    print(
        "  rescue     :",
        event[
            "rescue"
        ],
    )

    print(
        "  reason     :",
        event[
            "reason"
        ],
    )


lane_r2_rescued = any(
    event[
        "rescue"
    ]
    is True
    and
    event[
        "reason"
    ]
    == (
        "complete_catalog_identity_"
        "token_coverage"
    )
    for event
    in lane_r2_events
)


lane_pass = (
    lane_raw_rank is not None
    and lane_raw_rank <= 5
    and lane_qualified_rank is not None
    and lane_qualified_rank <= 5
    and lane_r2_rescued
)


print()
print(
    "R2 actually rescued Lane :",
    lane_r2_rescued,
)

print(
    "LIVE LANE GATE           :",
    "PASS"
    if lane_pass
    else "FAIL",
)


all_pass = (
    all_pass
    and lane_pass
)


# ============================================================
# B. REGRESSION CANARIES
# ============================================================

print()
print("=" * 76)
print(" B. PRODUCTION REGRESSION CANARIES")
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


for (
    name,
    query,
    target,
) in canaries:

    raw = search_catalog(
        query,
        db_path=DB,
        limit=100,
    )

    qualified = (
        qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=100,
        )
    )

    raw_rank = rank_of(
        raw,
        target,
    )

    qualified_rank = rank_of(
        qualified,
        target,
    )

    passed = (
        raw_rank is not None
        and raw_rank <= 5
        and qualified_rank is not None
        and qualified_rank <= 5
    )

    print()
    print(name)
    print(
        "  target ID       :",
        target,
    )
    print(
        "  raw rank        :",
        raw_rank,
    )
    print(
        "  qualified rank  :",
        qualified_rank,
    )
    print(
        "  PASS            :",
        passed,
    )

    report[
        "production_canaries"
    ].append(
        {
            "name":
                name,

            "query":
                query,

            "target_id":
                target,

            "raw_rank":
                raw_rank,

            "qualified_rank":
                qualified_rank,

            "pass":
                passed,
        }
    )

    all_pass = (
        all_pass
        and passed
    )


# ============================================================
# C. VERIFY R1F STILL OPERATES
# ============================================================

print()
print("=" * 76)
print(" C. R1F CONTENT RESCUE PRESERVATION")
print("=" * 76)

PYTHON_QUERY = (
    "AI assisted Python programming"
)

python_r1f = [
    event
    for event
    in r1f_events
    if (
        event[
            "query"
        ]
        == PYTHON_QUERY
        and
        event[
            "document_id"
        ]
        == 11
        and
        event[
            "rescue"
        ]
        is True
    )
]


print(
    "Python R1F rescue events:",
    len(
        python_r1f
    ),
)


for event in python_r1f:
    print(
        "  reason:",
        event[
            "reason"
        ],
    )


r1f_preserved = (
    len(
        python_r1f
    )
    >= 1
)


print(
    "R1F PRESERVED:",
    r1f_preserved,
)


all_pass = (
    all_pass
    and r1f_preserved
)


# ============================================================
# D. SEMANTIC REGRESSION
# ============================================================

print()
print("=" * 76)
print(" D. EXISTING SEMANTIC RECALL")
print("=" * 76)


semantic_queries = (
    "civil defense manual",
    "US Army survival manual",
    "practical electronics handbook",
    "Marx mathematical manuscripts",
)


for query in semantic_queries:

    raw = search_catalog(
        query,
        db_path=DB,
        limit=20,
    )

    qualified = (
        qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=20,
        )
    )

    passed = (
        bool(raw)
        and
        bool(qualified)
    )

    print()
    print(query)

    print(
        "  raw       :",
        len(raw),
    )

    print(
        "  qualified :",
        len(qualified),
    )

    print(
        "  PASS      :",
        passed,
    )

    report[
        "semantic_regression"
    ].append(
        {
            "query":
                query,

            "raw_count":
                len(raw),

            "qualified_count":
                len(qualified),

            "pass":
                passed,
        }
    )

    all_pass = (
        all_pass
        and passed
    )


# ============================================================
# E. ADVERSARIAL PRECISION
# ============================================================

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

    qualified = (
        qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=25,
        )
    )

    passed = (
        len(
            qualified
        )
        == 0
    )

    print()
    print(query)

    print(
        "  qualified :",
        len(
            qualified
        ),
    )

    print(
        "  PASS      :",
        passed,
    )

    report[
        "adversarial"
    ].append(
        {
            "query":
                query,

            "qualified_count":
                len(
                    qualified
                ),

            "pass":
                passed,
        }
    )

    all_pass = (
        all_pass
        and passed
    )


# ============================================================
# F. LIVE NEAR-MISS PRECISION
#
# These are executed through the actual production path.
#
# The gate here is NOT "zero results", because a near-miss
# query could legitimately retrieve some other catalog item.
#
# The requirement is specifically:
#
#   Lane ID 86876 must NOT be R2-rescued for the altered query.
# ============================================================

print()
print("=" * 76)
print(" F. LIVE LANE NEAR-MISS PRECISION")
print("=" * 76)


near_miss_queries = (
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
        "extra_term",
        (
            "Edward William Lane Arabic English "
            "Lexicon Vol 6 Supplement"
        ),
    ),

    (
        "revised",
        (
            "Edward William Lane Arabic English "
            "Lexicon Vol 6 Revised"
        ),
    ),
)


near_miss_pass = True


for (
    name,
    query,
) in near_miss_queries:

    start = len(
        r2_events
    )

    qualified = (
        qs.search_qualified_catalog(
            query,
            db_path=DB,
            limit=100,
        )
    )

    events = (
        r2_events[
            start:
        ]
    )

    lane_events = [
        event
        for event
        in events
        if (
            event[
                "document_id"
            ]
            == LANE_ID
        )
    ]

    lane_rescued = any(
        event[
            "rescue"
        ]
        is True
        for event
        in lane_events
    )

    passed = (
        not lane_rescued
    )

    near_miss_pass = (
        near_miss_pass
        and passed
    )

    print()
    print(name)

    print(
        "  query             :",
        query,
    )

    print(
        "  qualified results :",
        len(
            qualified
        ),
    )

    print(
        "  Lane R2 events    :",
        len(
            lane_events
        ),
    )

    print(
        "  Lane R2 rescued   :",
        lane_rescued,
    )

    print(
        "  PASS              :",
        passed,
    )


    report[
        "near_miss"
    ].append(
        {
            "name":
                name,

            "query":
                query,

            "qualified_count":
                len(
                    qualified
                ),

            "lane_r2_event_count":
                len(
                    lane_events
                ),

            "lane_r2_rescued":
                lane_rescued,

            "pass":
                passed,
        }
    )


all_pass = (
    all_pass
    and near_miss_pass
)


# ============================================================
# G. THRESHOLD IMMUTABILITY
# ============================================================

print()
print("=" * 76)
print(" G. THRESHOLD IMMUTABILITY")
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
    "minimum_phrase     :",
    engine.thresholds.minimum_phrase,
)

print(
    "PASS:",
    thresholds_pass,
)


all_pass = (
    all_pass
    and thresholds_pass
)


# ============================================================
# H. EVENT SUMMARY
# ============================================================

print()
print("=" * 76)
print(" H. LIVE RESCUE EVENT SUMMARY")
print("=" * 76)


r2_true = [
    event
    for event
    in r2_events
    if event[
        "rescue"
    ]
    is True
]

r1f_true = [
    event
    for event
    in r1f_events
    if event[
        "rescue"
    ]
    is True
]


print(
    "R1F calls observed :",
    len(
        r1f_events
    ),
)

print(
    "R1F rescues        :",
    len(
        r1f_true
    ),
)

print(
    "R2 calls observed  :",
    len(
        r2_events
    ),
)

print(
    "R2 rescues         :",
    len(
        r2_true
    ),
)


print()
print(
    "R2 RESCUE DOCUMENTS:"
)


seen = set()

for event in r2_true:

    key = (
        event[
            "query"
        ],
        event[
            "document_id"
        ],
        event[
            "title"
        ],
    )

    if key in seen:
        continue

    seen.add(key)

    print(
        "  query:",
        event[
            "query"
        ],
    )

    print(
        "    id    :",
        event[
            "document_id"
        ],
    )

    print(
        "    title :",
        event[
            "title"
        ],
    )

    print(
        "    reason:",
        event[
            "reason"
        ],
    )


# ============================================================
# I. REPORT
# ============================================================

report[
    "live_lane"
] = {
    "query":
        LANE_QUERY,

    "target_id":
        LANE_ID,

    "raw_rank":
        lane_raw_rank,

    "qualified_rank":
        lane_qualified_rank,

    "r1f_events":
        lane_r1f_events,

    "r2_events":
        lane_r2_events,

    "r2_rescued":
        lane_r2_rescued,

    "pass":
        lane_pass,
}


report[
    "summary"
] = {
    "lane_live_path_pass":
        lane_pass,

    "lane_r2_rescue_observed":
        lane_r2_rescued,

    "regression_canaries_pass":
        all(
            item[
                "pass"
            ]
            for item
            in report[
                "production_canaries"
            ]
        ),

    "r1f_preserved":
        r1f_preserved,

    "semantic_regression_pass":
        all(
            item[
                "pass"
            ]
            for item
            in report[
                "semantic_regression"
            ]
        ),

    "adversarial_precision_pass":
        all(
            item[
                "pass"
            ]
            for item
            in report[
                "adversarial"
            ]
        ),

    "near_miss_precision_pass":
        near_miss_pass,

    "thresholds_unchanged":
        thresholds_pass,

    "r1f_calls_observed":
        len(
            r1f_events
        ),

    "r1f_rescues":
        len(
            r1f_true
        ),

    "r2_calls_observed":
        len(
            r2_events
        ),

    "r2_rescues":
        len(
            r2_true
        ),

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


# ============================================================
# J. FINAL CERTIFICATION RESULT
# ============================================================

print()
print("=" * 76)
print(" GENESIS RECALL R2-R2A-R4-R5 RESULT")
print("=" * 76)

summary = report[
    "summary"
]

print(
    "Lane live production path :",
    summary[
        "lane_live_path_pass"
    ],
)

print(
    "Lane R2 rescue observed   :",
    summary[
        "lane_r2_rescue_observed"
    ],
)

print(
    "Regression canaries       :",
    summary[
        "regression_canaries_pass"
    ],
)

print(
    "R1F content rescue        :",
    summary[
        "r1f_preserved"
    ],
)

print(
    "Semantic regression       :",
    summary[
        "semantic_regression_pass"
    ],
)

print(
    "Adversarial precision     :",
    summary[
        "adversarial_precision_pass"
    ],
)

print(
    "Near-miss precision       :",
    summary[
        "near_miss_precision_pass"
    ],
)

print(
    "Thresholds unchanged      :",
    summary[
        "thresholds_unchanged"
    ],
)

print()

print(
    "R2-R2A-R4-R5 CERTIFIED    :",
    all_pass,
)

print("=" * 76)


raise SystemExit(
    0
    if all_pass
    else 1
)
