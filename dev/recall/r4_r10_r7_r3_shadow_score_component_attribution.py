from __future__ import annotations

import ast
import csv
import json
import sqlite3
import sys

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

SOURCE_HARNESS = (
    DEVDIR
    / "r4_r10_r7_r1_79286_tie_set.py"
)

INPUT = (
    OUTDIR
    / "r4_r10_r7_r2_rank_1_30_comparators.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r7_r3_shadow_score_component_attribution.json"
)

DETAIL = (
    OUTDIR
    / "r4_r10_r7_r3_score_component_detail.tsv"
)

CENSUS = (
    OUTDIR
    / "r4_r10_r7_r3_dominant_component_census.tsv"
)

TARGET_OUT = (
    OUTDIR
    / "r4_r10_r7_r3_target_79286_score_contract.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_r7_r3_score_attribution_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r7_r3_score_formula_contract.txt"
)


TARGET_ID = 79286
TARGET_RANK = 27

getcontext().prec = 60


# ============================================================
# HELPERS
# ============================================================

def D(value: Any) -> Decimal:
    return Decimal(str(value).strip())


def read_tsv(path: Path) -> list[dict[str, str]]:

    with path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:

    if not rows:
        path.write_text("", encoding="utf-8")
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


# ============================================================
# AST-CAPTURE EXACT SHADOW SCORE FORMULA
# ============================================================

source = SOURCE_HARNESS.read_text(
    encoding="utf-8"
)

tree = ast.parse(source)

shadow_rank_node = None

for node in ast.walk(tree):

    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "shadow_rank"
    ):
        shadow_rank_node = node
        break


if shadow_rank_node is None:
    raise RuntimeError("shadow_rank unavailable")


score_assignment = None

for node in ast.walk(shadow_rank_node):

    if not isinstance(node, ast.Assign):
        continue

    if len(node.targets) != 1:
        continue

    target = node.targets[0]

    if (
        isinstance(target, ast.Name)
        and target.id == "shadow_score"
    ):
        score_assignment = node
        break


if score_assignment is None:
    raise RuntimeError("shadow_score assignment unavailable")


formula_source = ast.unparse(
    score_assignment.value
)


# ============================================================
# EXPECTED FROZEN R7 FORMULA
# ============================================================

EXPECTED_WEIGHTS = {
    "coverage": Decimal("0.40"),
    "rarity_coverage": Decimal("0.27"),
    "title_coverage": Decimal("0.23"),
    "numeric_identity": Decimal("0.07"),
    "bm25_position": Decimal("0.03"),
}


for name, weight in EXPECTED_WEIGHTS.items():

    if name not in formula_source:
        raise RuntimeError(
            f"score formula missing {name}"
        )

    if str(weight) not in formula_source:
        # Decimal("0.40") string becomes 0.40
        # ast.unparse may normalize to 0.4.
        normalized = str(float(weight))

        if normalized not in formula_source:
            raise RuntimeError(
                f"weight contract missing {name}={weight}"
            )


# ============================================================
# LOAD EXACT RANK 1–30 POPULATION
# ============================================================

rows = read_tsv(INPUT)

if len(rows) != 30:
    raise RuntimeError(
        f"expected 30 comparator rows, got {len(rows)}"
    )


rows.sort(
    key=lambda row:
        int(row["original_r7_rank"])
)


target_matches = [
    row
    for row in rows
    if int(row["document_id"]) == TARGET_ID
]


if len(target_matches) != 1:
    raise RuntimeError(
        "79286 target missing or duplicated"
    )


target = target_matches[0]

if int(target["original_r7_rank"]) != TARGET_RANK:
    raise RuntimeError(
        "79286 rank contract changed"
    )


# ============================================================
# COMPONENT RECONSTRUCTION
# ============================================================

COMPONENT_FIELDS = (
    "coverage",
    "rarity_coverage",
    "title_coverage",
    "numeric_identity",
    "bm25_position",
)


def components(row: dict[str, str]) -> dict[str, Decimal]:

    # R7-R3-R2 certified input reconstruction:
    #
    # R7-R1 computes:
    #   bm25_position =
    #       1.0 - (ordinal - 1) / (len(rows) - 1)
    #
    # R7-R2 exports ordinal as production_rank.
    # Exact target-query candidate pool cardinality:
    #   len(rows) = 12000
    #
    # This reconstructs the ORIGINAL R7 signal only.
    # It does not alter any ranking score.
    production_rank = int(
        row["production_rank"]
    )

    bm25_position = Decimal("1") - (
        Decimal(
            production_rank - 1
        )
        /
        Decimal(
            12000 - 1
        )
    )

    raw = {
        "coverage":
            D(row["coverage"]),

        "rarity_coverage":
            D(row["rarity_coverage"]),

        "title_coverage":
            D(row["title_coverage"]),

        "numeric_identity":
            D(row["numeric_identity"]),

        "bm25_position":
            bm25_position,
    }

    weighted = {
        name:
            raw[name]
            * EXPECTED_WEIGHTS[name]
        for name in COMPONENT_FIELDS
    }

    reconstructed = sum(
        weighted.values(),
        Decimal("0")
    )

    stored = D(
        row["shadow_score"]
    )

    return {
        **{
            f"raw_{name}":
                raw[name]
            for name in COMPONENT_FIELDS
        },

        **{
            f"weighted_{name}":
                weighted[name]
            for name in COMPONENT_FIELDS
        },

        "reconstructed":
            reconstructed,

        "stored":
            stored,

        "reconstruction_error":
            reconstructed - stored,
    }


target_components = components(
    target
)


# ============================================================
# ATTRIBUTION AGAINST TARGET
# ============================================================

detail_rows = []
dominant_counter = Counter()

ahead = [
    row
    for row in rows
    if int(row["original_r7_rank"]) < TARGET_RANK
]


if len(ahead) != 26:
    raise RuntimeError(
        f"expected 26 rows ahead, got {len(ahead)}"
    )


max_reconstruction_error = Decimal("0")


for row in rows:

    values = components(
        row
    )

    candidate_id = int(
        row["document_id"]
    )


    component_deltas = {
        name:
            values[
                f"weighted_{name}"
            ]
            -
            target_components[
                f"weighted_{name}"
            ]
        for name in COMPONENT_FIELDS
    }


    total_component_delta = sum(
        component_deltas.values(),
        Decimal("0")
    )


    actual_score_delta = (
        values["stored"]
        -
        target_components["stored"]
    )


    attribution_error = (
        total_component_delta
        -
        actual_score_delta
    )


    max_reconstruction_error = max(
        max_reconstruction_error,
        abs(
            values["reconstruction_error"]
        ),
        abs(
            attribution_error
        ),
    )


    positive_deltas = [
        (
            name,
            delta,
        )
        for name, delta
        in component_deltas.items()
        if delta > 0
    ]


    if candidate_id == TARGET_ID:

        dominant_component = "TARGET"

    elif not positive_deltas:

        dominant_component = (
            "NO_POSITIVE_COMPONENT"
        )

    else:

        dominant_component = max(
            positive_deltas,
            key=lambda item:
                item[1],
        )[0]

        if int(
            row["original_r7_rank"]
        ) < TARGET_RANK:

            dominant_counter[
                dominant_component
            ] += 1


    detail_rows.append(
        {
            "rank":
                int(
                    row[
                        "original_r7_rank"
                    ]
                ),

            "document_id":
                candidate_id,

            "title":
                row["title"],

            "is_target":
                candidate_id == TARGET_ID,

            "stored_shadow_score":
                str(
                    values["stored"]
                ),

            "reconstructed_shadow_score":
                str(
                    values["reconstructed"]
                ),

            "reconstruction_error":
                str(
                    values[
                        "reconstruction_error"
                    ]
                ),

            "score_delta_vs_target":
                str(
                    actual_score_delta
                ),

            "coverage_raw":
                str(
                    values[
                        "raw_coverage"
                    ]
                ),

            "coverage_weighted":
                str(
                    values[
                        "weighted_coverage"
                    ]
                ),

            "coverage_delta":
                str(
                    component_deltas[
                        "coverage"
                    ]
                ),

            "rarity_raw":
                str(
                    values[
                        "raw_rarity_coverage"
                    ]
                ),

            "rarity_weighted":
                str(
                    values[
                        "weighted_rarity_coverage"
                    ]
                ),

            "rarity_delta":
                str(
                    component_deltas[
                        "rarity_coverage"
                    ]
                ),

            "title_raw":
                str(
                    values[
                        "raw_title_coverage"
                    ]
                ),

            "title_weighted":
                str(
                    values[
                        "weighted_title_coverage"
                    ]
                ),

            "title_delta":
                str(
                    component_deltas[
                        "title_coverage"
                    ]
                ),

            "numeric_raw":
                str(
                    values[
                        "raw_numeric_identity"
                    ]
                ),

            "numeric_weighted":
                str(
                    values[
                        "weighted_numeric_identity"
                    ]
                ),

            "numeric_delta":
                str(
                    component_deltas[
                        "numeric_identity"
                    ]
                ),

            "bm25_position_raw":
                str(
                    values[
                        "raw_bm25_position"
                    ]
                ),

            "bm25_position_weighted":
                str(
                    values[
                        "weighted_bm25_position"
                    ]
                ),

            "bm25_position_delta":
                str(
                    component_deltas[
                        "bm25_position"
                    ]
                ),

            "component_delta_sum":
                str(
                    total_component_delta
                ),

            "attribution_error":
                str(
                    attribution_error
                ),

            "dominant_positive_component":
                dominant_component,

            "production_rank":
                row[
                    "production_rank"
                ],

            "full_title_identity":
                row[
                    "full_title_identity"
                ],
        }
    )


# ============================================================
# TARGET CONTRACT
# ============================================================

target_out = [
    {
        "document_id":
            TARGET_ID,

        "rank":
            TARGET_RANK,

        "title":
            target["title"],

        "stored_shadow_score":
            str(
                target_components[
                    "stored"
                ]
            ),

        "reconstructed_shadow_score":
            str(
                target_components[
                    "reconstructed"
                ]
            ),

        "coverage_raw":
            str(
                target_components[
                    "raw_coverage"
                ]
            ),

        "coverage_weighted":
            str(
                target_components[
                    "weighted_coverage"
                ]
            ),

        "rarity_raw":
            str(
                target_components[
                    "raw_rarity_coverage"
                ]
            ),

        "rarity_weighted":
            str(
                target_components[
                    "weighted_rarity_coverage"
                ]
            ),

        "title_raw":
            str(
                target_components[
                    "raw_title_coverage"
                ]
            ),

        "title_weighted":
            str(
                target_components[
                    "weighted_title_coverage"
                ]
            ),

        "numeric_raw":
            str(
                target_components[
                    "raw_numeric_identity"
                ]
            ),

        "numeric_weighted":
            str(
                target_components[
                    "weighted_numeric_identity"
                ]
            ),

        "bm25_position_raw":
            str(
                target_components[
                    "raw_bm25_position"
                ]
            ),

        "bm25_position_weighted":
            str(
                target_components[
                    "weighted_bm25_position"
                ]
            ),

        "full_title_identity":
            target[
                "full_title_identity"
            ],
    }
]


# ============================================================
# CENSUS
# ============================================================

census_rows = []

for name, count in (
    dominant_counter.most_common()
):

    census_rows.append(
        {
            "dominant_positive_component":
                name,

            "count":
                count,

            "percent_of_26":
                round(
                    count
                    / 26.0
                    * 100.0,
                    4,
                ),
        }
    )


# ============================================================
# NEIGHBOR 26/27/28 DIFFERENTIAL
# ============================================================

by_rank = {
    row["rank"]:
        row
    for row in detail_rows
}


neighbor_26 = by_rank[26]
neighbor_27 = by_rank[27]
neighbor_28 = by_rank[28]


neighbor_contract = {
    "rank26_document":
        neighbor_26[
            "document_id"
        ],

    "rank27_document":
        neighbor_27[
            "document_id"
        ],

    "rank28_document":
        neighbor_28[
            "document_id"
        ],

    "rank26_score_delta":
        neighbor_26[
            "score_delta_vs_target"
        ],

    "rank28_score_delta":
        neighbor_28[
            "score_delta_vs_target"
        ],

    "rank26_bm25_delta":
        neighbor_26[
            "bm25_position_delta"
        ],

    "rank28_bm25_delta":
        neighbor_28[
            "bm25_position_delta"
        ],
}


# ============================================================
# ROOT CAUSE
# ============================================================

if not dominant_counter:

    dominant_component = "NONE"

else:

    dominant_component = (
        dominant_counter
        .most_common(1)[0][0]
    )


if dominant_component == "bm25_position":

    root_cause = (
        "BM25_POSITION_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER"
    )

elif dominant_component == "coverage":

    root_cause = (
        "COVERAGE_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER"
    )

elif dominant_component == "rarity_coverage":

    root_cause = (
        "RARITY_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER"
    )

elif dominant_component == "title_coverage":

    root_cause = (
        "TITLE_COVERAGE_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER"
    )

elif dominant_component == "numeric_identity":

    root_cause = (
        "NUMERIC_IDENTITY_COMPONENT_DOMINATES_SHADOW_SCORE_ORDER"
    )

else:

    root_cause = (
        "MIXED_OR_UNRESOLVED_SCORE_COMPONENT_DOMINANCE"
    )


# ============================================================
# READ-ONLY DB SAFETY
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

tolerance = Decimal("1e-12")


all_reconstruct = all(
    abs(
        D(
            row[
                "reconstruction_error"
            ]
        )
    )
    <= tolerance
    for row in detail_rows
)


all_attribution = all(
    abs(
        D(
            row[
                "attribution_error"
            ]
        )
    )
    <= tolerance
    for row in detail_rows
)


all_ahead_positive = all(
    D(
        row[
            "score_delta_vs_target"
        ]
    )
    > 0
    for row in detail_rows
    if row["rank"] < TARGET_RANK
)


certification = {
    "exact_rank_1_30_population":
        len(
            detail_rows
        )
        == 30,

    "exact_26_documents_ahead":
        len(
            ahead
        )
        == 26,

    "target_79286_rank_27":
        int(
            target[
                "original_r7_rank"
            ]
        )
        == 27,

    "formula_ast_captured":
        bool(
            formula_source
        ),

    "all_scores_reconstructed":
        all_reconstruct,

    "all_component_deltas_reconcile":
        all_attribution,

    "all_26_ahead_have_positive_score_delta":
        all_ahead_positive,

    "dominant_component_identified":
        dominant_component
        != "NONE",

    "database_integrity":
        integrity == "ok",
}


diagnostic_certified = all(
    certification.values()
)


# ============================================================
# REPORT
# ============================================================

report = {
    "phase":
        "Genesis Recall R4-R10-R7-R3",

    "target": {
        "document_id":
            TARGET_ID,

        "rank":
            TARGET_RANK,

        "shadow_score":
            str(
                target_components[
                    "stored"
                ]
            ),
    },

    "score_formula": {
        "source":
            formula_source,

        "weights":
            {
                name:
                    str(weight)
                for name, weight
                in EXPECTED_WEIGHTS.items()
            },
    },

    "population": {
        "rank_1_30":
            len(
                detail_rows
            ),

        "documents_ahead":
            len(
                ahead
            ),
    },

    "dominant_component_census":
        dict(
            dominant_counter
        ),

    "dominant_component":
        dominant_component,

    "root_cause":
        root_cause,

    "neighbor_contract":
        neighbor_contract,

    "max_arithmetic_error":
        str(
            max_reconstruction_error
        ),

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
    DETAIL,
    detail_rows,
)

write_tsv(
    CENSUS,
    census_rows,
)

write_tsv(
    TARGET_OUT,
    target_out,
)


# ============================================================
# TRACE
# ============================================================

trace_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R7-R3",
    " SHADOW-SCORE COMPONENT ATTRIBUTION",
    "=" * 78,
    "",
    "FORMULA",
    f"  {formula_source}",
    "",
    "TARGET 79286",
]


for row in target_out:
    for key, value in row.items():
        trace_lines.append(
            f"  {key:<28}: {value}"
        )


trace_lines.extend(
    (
        "",
        "DOMINANT COMPONENT — 26 DOCUMENTS AHEAD",
    )
)


for name, count in dominant_counter.most_common():

    trace_lines.append(
        f"  {name:<28}: {count}"
    )


trace_lines.extend(
    (
        "",
        "NEIGHBOR CONTRACT",
    )
)


for key, value in neighbor_contract.items():

    trace_lines.append(
        f"  {key:<28}: {value}"
    )


trace_lines.extend(
    (
        "",
        f"DOMINANT COMPONENT : {dominant_component}",
        f"ROOT CAUSE         : {root_cause}",
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
        f"R7-R3 DIAGNOSTIC CERTIFIED : {diagnostic_certified}",
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
            " GENESIS RECALL R4-R10-R7-R3",
            " SHADOW SCORE FORMULA CONTRACT",
            "=" * 78,
            "",
            f"source harness : {SOURCE_HARNESS}",
            "",
            "AST FORMULA:",
            f"  shadow_score = {formula_source}",
            "",
            "WEIGHTS:",
            *(
                f"  {name:<24} {weight}"
                for name, weight
                in EXPECTED_WEIGHTS.items()
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
print(" GENESIS RECALL R4-R10-R7-R3 RESULT")
print("=" * 78)

print()
print("SHADOW SCORE FORMULA")
print(" ", formula_source)

print()
print("TARGET 79286")

for key, value in target_out[0].items():
    print(
        f"  {key:<28}: {value}"
    )

print()
print("26 DOCUMENTS AHEAD — DOMINANT POSITIVE COMPONENT")

for name, count in dominant_counter.most_common():
    print(
        f"  {name:<28}: {count}"
    )

print()
print("NEIGHBOR 26 / 27 / 28")

for key, value in neighbor_contract.items():
    print(
        f"  {key:<28}: {value}"
    )

print()
print("ROOT CAUSE")
print("  dominant component :", dominant_component)
print("  root cause         :", root_cause)

print()
print("CERTIFICATION")

for key, value in certification.items():
    print(
        f"  {key:<42}: {value}"
    )

print()
print(
    "R4-R10-R7-R3 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)

print()
print("Artifacts:")
print(" ", REPORT)
print(" ", DETAIL)
print(" ", CENSUS)
print(" ", TARGET_OUT)
print(" ", TRACE)
print(" ", SOURCE_MAP)

print("=" * 78)

raise SystemExit(
    0
    if diagnostic_certified
    else 1
)
