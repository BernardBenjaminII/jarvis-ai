from __future__ import annotations

import ast
import csv
import json
import sqlite3
import sys
import time

from collections import Counter
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"
DEVDIR = PROJECT / "dev/recall"

R7R1_REPORT = (
    OUTDIR
    / "r4_r10_r7_r1_79286_tie_set.json"
)

R7R1_TIESET = (
    OUTDIR
    / "r4_r10_r7_r1_79286_tie_set.tsv"
)

R7R1_HARNESS = (
    DEVDIR
    / "r4_r10_r7_r1_79286_tie_set.py"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_r2_sort_key_dominance.json"
)

COMPARATORS = (
    OUTDIR
    / "r4_r10_r7_r2_rank_1_30_comparators.tsv"
)

DIFFERENCES = (
    OUTDIR
    / "r4_r10_r7_r2_first_difference_census.tsv"
)

TARGET_OUT = (
    OUTDIR
    / "r4_r10_r7_r2_target_79286_contract.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_r7_r2_sort_key_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r7_r2_sort_contract.txt"
)


TARGET_ID = 79286
EXPECTED_TARGET_RANK = 27

getcontext().prec = 50


# ============================================================
# IO
# ============================================================

def read_tsv(
    path: Path,
) -> list[dict[str, str]]:

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

            if key in seen:
                continue

            seen.add(
                key
            )

            fields.append(
                key
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
        writer.writerows(
            rows
        )


# ============================================================
# DECIMAL CONTRACT
# ============================================================

def D(
    value: Any,
) -> Decimal:

    raw = str(
        value
    ).strip()

    if not raw:
        return Decimal("0")

    return Decimal(
        raw
    )


# ============================================================
# STATIC SORT-KEY CONTRACT FROM R7-R1 HARNESS
# ============================================================

source = R7R1_HARNESS.read_text(
    encoding="utf-8"
)

tree = ast.parse(
    source
)


shadow_rank_node = None


for node in ast.walk(
    tree
):

    if (
        isinstance(
            node,
            ast.FunctionDef,
        )
        and
        node.name == "shadow_rank"
    ):

        shadow_rank_node = node
        break


if shadow_rank_node is None:

    raise RuntimeError(
        "shadow_rank function not found"
    )


sort_lambda = None


for node in ast.walk(
    shadow_rank_node
):

    if not isinstance(
        node,
        ast.Call,
    ):
        continue

    if not isinstance(
        node.func,
        ast.Attribute,
    ):
        continue

    if node.func.attr != "sort":
        continue


    for keyword in node.keywords:

        if (
            keyword.arg == "key"
            and
            isinstance(
                keyword.value,
                ast.Lambda,
            )
        ):

            sort_lambda = (
                keyword.value
            )

            break


if sort_lambda is None:

    raise RuntimeError(
        "shadow_rank sort-key lambda not found"
    )


if not isinstance(
    sort_lambda.body,
    ast.Tuple,
):

    raise RuntimeError(
        "shadow_rank key is not tuple"
    )


sort_key_source = [
    ast.unparse(
        element
    )
    for element in sort_lambda.body.elts
]


expected_sort_key = [
    "-item.shadow_score",
    "-item.coverage",
    "-item.rarity_coverage",
    "-item.title_coverage",
    "-item.numeric_identity",
    "-item.full_title_identity",
    "item.production_rank",
    "item.document_id",
    "item.chunk_id",
]


if sort_key_source != expected_sort_key:

    raise RuntimeError(
        "unexpected R7-R1 sort-key contract:\n"
        + repr(
            sort_key_source
        )
    )


# ============================================================
# LOAD TIE SET
# ============================================================

rows = read_tsv(
    R7R1_TIESET
)


window = [
    row
    for row in rows
    if 1
    <= int(
        row[
            "original_r7_rank"
        ]
    )
    <= 30
]


window.sort(
    key=lambda row:
        int(
            row[
                "original_r7_rank"
            ]
        )
)


if len(
    window
) != 30:

    raise RuntimeError(
        f"expected exact rank-1–30 window, got {len(window)}"
    )


target_matches = [
    row
    for row in window
    if int(
        row[
            "document_id"
        ]
    )
    == TARGET_ID
]


if len(
    target_matches
) != 1:

    raise RuntimeError(
        "79286 target row unavailable or duplicated"
    )


target = target_matches[
    0
]


if int(
    target[
        "original_r7_rank"
    ]
) != EXPECTED_TARGET_RANK:

    raise RuntimeError(
        "79286 original rank contract changed"
    )


# ============================================================
# EXACT SORT VECTOR
# ============================================================

NUMERIC_FIELDS = (
    "shadow_score",
    "coverage",
    "rarity_coverage",
    "title_coverage",
    "numeric_identity",
    "full_title_identity",
    "production_chunk_rank",
)


def vector(
    row: dict[str, str],
) -> dict[str, Any]:

    return {
        "shadow_score":
            D(
                row[
                    "shadow_score"
                ]
            ),

        "coverage":
            D(
                row[
                    "coverage"
                ]
            ),

        "rarity_coverage":
            D(
                row[
                    "rarity_coverage"
                ]
            ),

        "title_coverage":
            D(
                row[
                    "title_coverage"
                ]
            ),

        "numeric_identity":
            D(
                row[
                    "numeric_identity"
                ]
            ),

        "full_title_identity":
            D(
                row[
                    "full_title_identity"
                ]
            ),

        "production_rank":
            int(
                row[
                    "production_chunk_rank"
                ]
            ),

        "document_id":
            int(
                row[
                    "document_id"
                ]
            ),

        "chunk_id":
            int(
                row[
                    "chunk_id"
                ]
            ),
    }


target_vector = vector(
    target
)


# ============================================================
# COMPARISON LOGIC
# ============================================================
#
# Sort precedence:
#
#   higher shadow_score wins
#   higher coverage wins
#   higher rarity_coverage wins
#   higher title_coverage wins
#   higher numeric_identity wins
#   higher full_title_identity wins
#   lower production_rank wins
#   lower document_id wins
#   lower chunk_id wins
#
# ============================================================

precedence = (
    (
        "shadow_score",
        "DESC",
    ),
    (
        "coverage",
        "DESC",
    ),
    (
        "rarity_coverage",
        "DESC",
    ),
    (
        "title_coverage",
        "DESC",
    ),
    (
        "numeric_identity",
        "DESC",
    ),
    (
        "full_title_identity",
        "DESC",
    ),
    (
        "production_rank",
        "ASC",
    ),
    (
        "document_id",
        "ASC",
    ),
    (
        "chunk_id",
        "ASC",
    ),
)


def compare_field(
    field: str,
    direction: str,
    candidate_value: Any,
    target_value: Any,
) -> str:

    if candidate_value == target_value:
        return "TIE"

    if direction == "DESC":

        return (
            "CANDIDATE_WINS"
            if candidate_value > target_value
            else "TARGET_WINS"
        )

    return (
        "CANDIDATE_WINS"
        if candidate_value < target_value
        else "TARGET_WINS"
    )


def first_difference(
    candidate: dict[str, Any],
    target_value: dict[str, Any],
) -> tuple[
    str,
    str,
    Any,
    Any,
]:

    for field, direction in precedence:

        candidate_value = candidate[
            field
        ]

        target_field_value = target_value[
            field
        ]


        relation = compare_field(
            field,
            direction,
            candidate_value,
            target_field_value,
        )


        if relation != "TIE":

            return (
                field,
                relation,
                candidate_value,
                target_field_value,
            )


    return (
        "EXACT_SORT_KEY_TIE",
        "TIE",
        "",
        "",
    )


# ============================================================
# BUILD EXACT COMPARATOR ANATOMY
# ============================================================

comparators = []

difference_counter = Counter()

strict_primary_score_ahead = 0
exact_primary_score_ties = 0
near_primary_score_ties_1e12 = 0
near_primary_score_ties_1e9 = 0

true_full_feature_ties = 0


target_score = target_vector[
    "shadow_score"
]


target_core = (
    target_vector[
        "shadow_score"
    ],
    target_vector[
        "coverage"
    ],
    target_vector[
        "rarity_coverage"
    ],
    target_vector[
        "title_coverage"
    ],
    target_vector[
        "numeric_identity"
    ],
    target_vector[
        "full_title_identity"
    ],
)


for row in window:

    candidate_id = int(
        row[
            "document_id"
        ]
    )


    candidate_vector = vector(
        row
    )


    (
        first_field,
        relation,
        candidate_first_value,
        target_first_value,
    ) = first_difference(
        candidate_vector,
        target_vector,
    )


    if candidate_id != TARGET_ID:

        difference_counter[
            first_field
        ] += 1


    score_delta = (
        candidate_vector[
            "shadow_score"
        ]
        -
        target_score
    )


    absolute_score_delta = abs(
        score_delta
    )


    exact_score_tie = (
        candidate_vector[
            "shadow_score"
        ]
        ==
        target_score
    )


    near_1e12 = (
        absolute_score_delta
        <= Decimal(
            "1e-12"
        )
    )


    near_1e9 = (
        absolute_score_delta
        <= Decimal(
            "1e-9"
        )
    )


    candidate_core = (
        candidate_vector[
            "shadow_score"
        ],
        candidate_vector[
            "coverage"
        ],
        candidate_vector[
            "rarity_coverage"
        ],
        candidate_vector[
            "title_coverage"
        ],
        candidate_vector[
            "numeric_identity"
        ],
        candidate_vector[
            "full_title_identity"
        ],
    )


    full_feature_tie = (
        candidate_core
        ==
        target_core
    )


    if candidate_id != TARGET_ID:

        if (
            candidate_vector[
                "shadow_score"
            ]
            >
            target_score
        ):

            strict_primary_score_ahead += 1


        if exact_score_tie:

            exact_primary_score_ties += 1


        if near_1e12:

            near_primary_score_ties_1e12 += 1


        if near_1e9:

            near_primary_score_ties_1e9 += 1


        if full_feature_tie:

            true_full_feature_ties += 1


    comparators.append(
        {
            "original_r7_rank":
                int(
                    row[
                        "original_r7_rank"
                    ]
                ),

            "r7_r1_rank":
                int(
                    row[
                        "r7_r1_rank"
                    ]
                ),

            "document_id":
                candidate_id,

            "chunk_id":
                int(
                    row[
                        "chunk_id"
                    ]
                ),

            "title":
                row[
                    "title"
                ],

            "is_target_79286":
                candidate_id
                == TARGET_ID,

            "shadow_score":
                str(
                    candidate_vector[
                        "shadow_score"
                    ]
                ),

            "target_shadow_score":
                str(
                    target_score
                ),

            "score_delta_vs_target":
                str(
                    score_delta
                ),

            "absolute_score_delta":
                str(
                    absolute_score_delta
                ),

            "exact_primary_score_tie":
                exact_score_tie,

            "near_primary_score_tie_1e12":
                near_1e12,

            "near_primary_score_tie_1e9":
                near_1e9,

            "coverage":
                str(
                    candidate_vector[
                        "coverage"
                    ]
                ),

            "rarity_coverage":
                str(
                    candidate_vector[
                        "rarity_coverage"
                    ]
                ),

            "title_coverage":
                str(
                    candidate_vector[
                        "title_coverage"
                    ]
                ),

            "numeric_identity":
                str(
                    candidate_vector[
                        "numeric_identity"
                    ]
                ),

            "full_title_identity":
                str(
                    candidate_vector[
                        "full_title_identity"
                    ]
                ),

            "production_rank":
                candidate_vector[
                    "production_rank"
                ],

            "document_sort_id":
                candidate_vector[
                    "document_id"
                ],

            "chunk_sort_id":
                candidate_vector[
                    "chunk_id"
                ],

            "full_feature_tie":
                full_feature_tie,

            "first_differentiating_field":
                (
                    "TARGET"
                    if candidate_id
                    == TARGET_ID
                    else first_field
                ),

            "first_difference_relation":
                (
                    "TARGET"
                    if candidate_id
                    == TARGET_ID
                    else relation
                ),

            "candidate_first_value":
                (
                    ""
                    if candidate_id
                    == TARGET_ID
                    else str(
                        candidate_first_value
                    )
                ),

            "target_first_value":
                (
                    ""
                    if candidate_id
                    == TARGET_ID
                    else str(
                        target_first_value
                    )
                ),

            "full_query_tokens":
                row[
                    "full_query_tokens"
                ],

            "full_title_tokens":
                row[
                    "full_title_tokens"
                ],

            "full_matched_tokens":
                row[
                    "full_matched_tokens"
                ],
        }
    )


# ============================================================
# ONLY CANDIDATES AHEAD OF TARGET
# ============================================================

ahead = [
    row
    for row in comparators
    if int(
        row[
            "original_r7_rank"
        ]
    )
    < EXPECTED_TARGET_RANK
]


if len(
    ahead
) != 26:

    raise RuntimeError(
        f"expected 26 documents ahead of target; got {len(ahead)}"
    )


ahead_difference_counter = Counter(
    row[
        "first_differentiating_field"
    ]
    for row in ahead
)


ahead_candidate_wins = sum(
    1
    for row in ahead
    if row[
        "first_difference_relation"
    ]
    == "CANDIDATE_WINS"
)


if ahead_candidate_wins != 26:

    raise RuntimeError(
        "sort comparator contradiction: "
        f"only {ahead_candidate_wins}/26 ahead candidates "
        "win their first differing key"
    )


# ============================================================
# DOMINANT CAUSE
# ============================================================

if not ahead_difference_counter:

    dominant_field = "NONE"

else:

    dominant_field = (
        ahead_difference_counter
        .most_common(
            1
        )[0][0]
    )


if dominant_field == "shadow_score":

    dominant_cause = (
        "PRIMARY_SHADOW_SCORE_DOMINATES_79286"
    )


elif dominant_field == "bm25_position":

    dominant_cause = (
        "BM25_COMPONENT_DOMINATES_79286"
    )


elif dominant_field == "production_rank":

    dominant_cause = (
        "PRODUCTION_RANK_TIEBREAK_DOMINATES_79286"
    )


elif dominant_field == "full_title_identity":

    dominant_cause = (
        "FULL_TITLE_IDENTITY_DIFFERENTIAL"
    )


elif dominant_field == "EXACT_SORT_KEY_TIE":

    dominant_cause = (
        "EXACT_SORT_KEY_COLLISION"
    )


else:

    dominant_cause = (
        "FEATURE_PRECEDENCE_"
        + dominant_field.upper()
    )


# ============================================================
# TARGET CONTRACT ROW
# ============================================================

target_rows_out = [
    {
        "document_id":
            TARGET_ID,

        "original_r7_rank":
            int(
                target[
                    "original_r7_rank"
                ]
            ),

        "r7_r1_rank":
            int(
                target[
                    "r7_r1_rank"
                ]
            ),

        "title":
            target[
                "title"
            ],

        "shadow_score":
            str(
                target_vector[
                    "shadow_score"
                ]
            ),

        "coverage":
            str(
                target_vector[
                    "coverage"
                ]
            ),

        "rarity_coverage":
            str(
                target_vector[
                    "rarity_coverage"
                ]
            ),

        "title_coverage":
            str(
                target_vector[
                    "title_coverage"
                ]
            ),

        "numeric_identity":
            str(
                target_vector[
                    "numeric_identity"
                ]
            ),

        "full_title_identity":
            str(
                target_vector[
                    "full_title_identity"
                ]
            ),

        "production_rank":
            target_vector[
                "production_rank"
            ],

        "chunk_id":
            target_vector[
                "chunk_id"
            ],

        "full_query_tokens":
            target[
                "full_query_tokens"
            ],

        "full_title_tokens":
            target[
                "full_title_tokens"
            ],

        "full_matched_tokens":
            target[
                "full_matched_tokens"
            ],
    }
]


# ============================================================
# DIFFERENCE CENSUS
# ============================================================

difference_rows = []


for field, count in (
    ahead_difference_counter
    .most_common()
):

    difference_rows.append(
        {
            "first_differentiating_field":
                field,

            "count":
                count,

            "percent_of_26":
                round(
                    (
                        count
                        / 26.0
                    )
                    * 100.0,
                    4,
                ),
        }
    )


# ============================================================
# STATIC SAFETY — DATABASE READ ONLY
# ============================================================

conn = sqlite3.connect(
    f"file:{DB}?mode=ro",
    uri=True,
)

try:

    conn.execute(
        "PRAGMA query_only=ON"
    )

    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

finally:

    conn.close()


# ============================================================
# CERTIFICATION
# ============================================================

certification = {
    "exact_rank_1_30_window":
        len(
            window
        )
        == 30,

    "target_79286_rank_27":
        int(
            target[
                "original_r7_rank"
            ]
        )
        == 27,

    "exact_26_documents_ahead":
        len(
            ahead
        )
        == 26,

    "all_26_sort_dominance_explained":
        ahead_candidate_wins
        == 26,

    "sort_key_contract_captured":
        sort_key_source
        == expected_sort_key,

    "first_difference_census_complete":
        sum(
            ahead_difference_counter.values()
        )
        == 26,

    "database_integrity":
        integrity
        == "ok",
}


diagnostic_certified = all(
    certification.values()
)


# ============================================================
# REPORT
# ============================================================

report = {
    "phase":
        "Genesis Recall R4-R10-R7-R2",

    "target": {
        "document_id":
            TARGET_ID,

        "original_r7_rank":
            int(
                target[
                    "original_r7_rank"
                ]
            ),

        "r7_r1_rank":
            int(
                target[
                    "r7_r1_rank"
                ]
            ),

        "shadow_score":
            str(
                target_score
            ),

        "full_title_identity":
            str(
                target_vector[
                    "full_title_identity"
                ]
            ),
    },

    "window": {
        "rank_start":
            1,

        "rank_end":
            30,

        "rows":
            len(
                window
            ),

        "documents_ahead":
            len(
                ahead
            ),
    },

    "sort_key_contract":
        sort_key_source,

    "ahead_first_difference_census":
        dict(
            ahead_difference_counter
        ),

    "score_relationship": {
        "strict_primary_score_ahead":
            sum(
                1
                for row in ahead
                if D(
                    row[
                        "shadow_score"
                    ]
                )
                >
                target_score
            ),

        "exact_primary_score_ties":
            sum(
                1
                for row in ahead
                if row[
                    "exact_primary_score_tie"
                ]
            ),

        "near_primary_score_ties_1e12":
            sum(
                1
                for row in ahead
                if row[
                    "near_primary_score_tie_1e12"
                ]
            ),

        "near_primary_score_ties_1e9":
            sum(
                1
                for row in ahead
                if row[
                    "near_primary_score_tie_1e9"
                ]
            ),

        "full_feature_ties":
            sum(
                1
                for row in ahead
                if row[
                    "full_feature_tie"
                ]
            ),
    },

    "dominant_first_difference":
        dominant_field,

    "dominant_cause":
        dominant_cause,

    "certification":
        certification,

    "diagnostic_certified":
        diagnostic_certified,
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
    COMPARATORS,
    comparators,
)

write_tsv(
    DIFFERENCES,
    difference_rows,
)

write_tsv(
    TARGET_OUT,
    target_rows_out,
)


# ============================================================
# HUMAN TRACE
# ============================================================

trace_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R7-R2",
    " 79286 EXACT SORT-KEY DOMINANCE",
    "=" * 78,
    "",
    "TARGET",
    f"  document_id              : {TARGET_ID}",
    f"  original R7 rank         : {target['original_r7_rank']}",
    f"  R7-R1 rank               : {target['r7_r1_rank']}",
    f"  title                     : {target['title']}",
    f"  shadow score              : {target_vector['shadow_score']}",
    f"  coverage                  : {target_vector['coverage']}",
    f"  rarity coverage           : {target_vector['rarity_coverage']}",
    f"  title coverage            : {target_vector['title_coverage']}",
    f"  numeric identity          : {target_vector['numeric_identity']}",
    f"  full title identity       : {target_vector['full_title_identity']}",
    f"  production rank           : {target_vector['production_rank']}",
    "",
    "SORT KEY",
]


for item in sort_key_source:

    trace_lines.append(
        f"  {item}"
    )


trace_lines.extend(
    (
        "",
        "FIRST DIFFERENTIATING FIELD — 26 DOCUMENTS AHEAD",
    )
)


for field, count in (
    ahead_difference_counter
    .most_common()
):

    trace_lines.append(
        f"  {field:<28} : {count}"
    )


trace_lines.extend(
    (
        "",
        "PRIMARY SCORE RELATIONSHIP",
        (
            "  strict score greater       : "
            + str(
                report[
                    "score_relationship"
                ][
                    "strict_primary_score_ahead"
                ]
            )
        ),
        (
            "  exact score ties           : "
            + str(
                report[
                    "score_relationship"
                ][
                    "exact_primary_score_ties"
                ]
            )
        ),
        (
            "  near ties <=1e-12          : "
            + str(
                report[
                    "score_relationship"
                ][
                    "near_primary_score_ties_1e12"
                ]
            )
        ),
        (
            "  near ties <=1e-9           : "
            + str(
                report[
                    "score_relationship"
                ][
                    "near_primary_score_ties_1e9"
                ]
            )
        ),
        (
            "  full feature ties          : "
            + str(
                report[
                    "score_relationship"
                ][
                    "full_feature_ties"
                ]
            )
        ),
        "",
        f"DOMINANT FIRST DIFFERENCE : {dominant_field}",
        f"DOMINANT CAUSE            : {dominant_cause}",
        "",
        "CERTIFICATION",
    )
)


for key, value in certification.items():

    trace_lines.append(
        f"  {key:<42}: {value}"
    )


trace_lines.extend(
    (
        "",
        f"R7-R2 DIAGNOSTIC CERTIFIED : {diagnostic_certified}",
    )
)


TRACE.write_text(
    "\n".join(
        trace_lines
    )
    + "\n",
    encoding="utf-8",
)


SOURCE_MAP.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R7-R2",
            " EXACT SORT-KEY CONTRACT",
            "=" * 78,
            "",
            "SOURCE HARNESS:",
            str(
                R7R1_HARNESS
            ),
            "",
            "AST-RESOLVED SORT KEY:",
            *(
                f"  {index:02d}. {value}"
                for index, value
                in enumerate(
                    sort_key_source,
                    start=1,
                )
            ),
            "",
            "EXPECTED:",
            *(
                f"  {index:02d}. {value}"
                for index, value
                in enumerate(
                    expected_sort_key,
                    start=1,
                )
            ),
            "",
            "PRECEDENCE INTERPRETATION:",
            *(
                f"  {field:<24} {direction}"
                for field, direction
                in precedence
            ),
        )
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# CONSOLE
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R10-R7-R2 RESULT")
print("=" * 78)

print()
print("TARGET 79286")

print(
    "  original R7 rank           :",
    target[
        "original_r7_rank"
    ],
)

print(
    "  R7-R1 rank                 :",
    target[
        "r7_r1_rank"
    ],
)

print(
    "  shadow score               :",
    target_vector[
        "shadow_score"
    ],
)

print(
    "  full title identity        :",
    target_vector[
        "full_title_identity"
    ],
)

print(
    "  production rank            :",
    target_vector[
        "production_rank"
    ],
)


print()
print("EXACT SORT KEY")

for index, item in enumerate(
    sort_key_source,
    start=1,
):

    print(
        f"  {index:02d}. {item}"
    )


print()
print("26 DOCUMENTS AHEAD — FIRST DIFFERENTIATING FIELD")

for field, count in (
    ahead_difference_counter
    .most_common()
):

    print(
        f"  {field:<30}: {count}"
    )


print()
print("PRIMARY SCORE RELATIONSHIP")

print(
    "  strict score > target      :",
    report[
        "score_relationship"
    ][
        "strict_primary_score_ahead"
    ],
)

print(
    "  exact score ties           :",
    report[
        "score_relationship"
    ][
        "exact_primary_score_ties"
    ],
)

print(
    "  near ties <= 1e-12         :",
    report[
        "score_relationship"
    ][
        "near_primary_score_ties_1e12"
    ],
)

print(
    "  near ties <= 1e-9          :",
    report[
        "score_relationship"
    ][
        "near_primary_score_ties_1e9"
    ],
)

print(
    "  full feature ties          :",
    report[
        "score_relationship"
    ][
        "full_feature_ties"
    ],
)


print()
print("ROOT CAUSE")

print(
    "  dominant first difference  :",
    dominant_field,
)

print(
    "  dominant cause             :",
    dominant_cause,
)


print()
print("CERTIFICATION")

for key, value in certification.items():

    print(
        f"  {key:<42}: {value}"
    )


print()
print(
    "R4-R10-R7-R2 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)

print()
print("Artifacts:")
print(" ", REPORT)
print(" ", COMPARATORS)
print(" ", DIFFERENCES)
print(" ", TARGET_OUT)
print(" ", TRACE)
print(" ", SOURCE_MAP)

print("=" * 78)


raise SystemExit(
    0
    if diagnostic_certified
    else 1
)
