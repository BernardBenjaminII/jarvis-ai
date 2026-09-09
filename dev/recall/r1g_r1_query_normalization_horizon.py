from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import time

from collections import Counter
from pathlib import Path
from typing import Any


SCHEMA = "genesis-recall-r1g-r1-v2"

HORIZONS = (
    25,
    50,
    100,
    250,
    500,
)

EXTENSIONS = (
    ".pdf",
    ".txt",
    ".html",
    ".htm",
    ".epub",
    ".mobi",
    ".azw",
    ".azw3",
    ".doc",
    ".docx",
    ".rtf",
    ".md",
)

KNOWN = (
    {
        "name": "ai_assisted_python",
        "query": "AI assisted Python programming",
        "runtime_id": 11,
    },
    {
        "name": "cpp_programming",
        "query": "C++ programming",
        "runtime_id": 4,
    },
    {
        "name": "effective_c",
        "query": "effective C programming",
        "runtime_id": 14,
    },
    {
        "name": "civil_defense",
        "query": "civil defense manual",
        "runtime_id": 18,
    },
    {
        "name": "army_survival",
        "query": "US Army survival manual",
        "runtime_id": 32,
    },
    {
        "name": "practical_electronics",
        "query": "practical electronics handbook",
        "runtime_id": 42,
    },
    {
        "name": "marx_mathematics",
        "query": "Marx mathematical manuscripts",
        "runtime_id": 89330,
    },
)

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


# ============================================================
# QUERY NORMALIZATION
# ============================================================

def strip_extensions(text: str) -> str:

    value = str(
        text or ""
    ).strip()

    changed = True

    while changed:

        changed = False

        folded = value.casefold()

        for ext in EXTENSIONS:

            if folded.endswith(ext):

                value = value[
                    : -len(ext)
                ].rstrip(
                    " ._-"
                )

                changed = True
                break

    return value


def normalize_query(query: str) -> str:
    """
    Shadow-only normalization.

    Removes filename artifacts without destroying useful
    technical tokens such as C++, C#, XSS, or transliterated
    names.
    """

    value = strip_extensions(
        query
    )

    # Dotted filename chains:
    # foo.bar.baz -> foo bar baz
    value = re.sub(
        r"(?<=[A-Za-z])\.(?=[A-Za-z])",
        " ",
        value,
    )

    value = re.sub(
        r"(?<=[A-Za-z])\.(?=\d)",
        " ",
        value,
    )

    value = re.sub(
        r"(?<=\d)\.(?=[A-Za-z])",
        " ",
        value,
    )

    value = re.sub(
        r"[()\[\]{}:,;/\\|]+",
        " ",
        value,
    )

    value = re.sub(
        r"_+",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


def relaxed_query(query: str) -> str:

    value = normalize_query(
        query
    )

    value = re.sub(
        r"\b(?:vol(?:ume)?|ver(?:sion)?)\.?\s*\d+\b",
        " ",
        value,
        flags=re.I,
    )

    value = re.sub(
        r"\b\d+\.\d+\b",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


def query_variants(
    query: str,
) -> list[str]:

    variants: list[str] = []

    def add(value: str) -> None:

        value = value.strip()

        if not value:
            return

        folded = value.casefold()

        if folded not in {
            existing.casefold()
            for existing in variants
        }:
            variants.append(
                value
            )

    add(query)
    add(normalize_query(query))
    add(relaxed_query(query))

    return variants


# ============================================================
# SQLITE / IDENTITY
# ============================================================

def ro(path: Path) -> sqlite3.Connection:

    con = sqlite3.connect(
        f"file:{path.resolve()}?mode=ro",
        uri=True,
    )

    con.row_factory = sqlite3.Row

    con.execute(
        "PRAGMA query_only=ON"
    )

    con.execute(
        "PRAGMA busy_timeout=10000"
    )

    return con


def runtime_document(
    con: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any] | None:

    row = con.execute(
        """
        SELECT
            id,
            title,
            file_path,
            sha256,
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


def identity_family(
    con: sqlite3.Connection,
    sha256: str,
) -> set[int]:

    rows = con.execute(
        """
        SELECT id
        FROM runtime_documents
        WHERE sha256=?
        ORDER BY id
        """,
        (sha256,),
    ).fetchall()

    return {
        int(row["id"])
        for row in rows
    }


def result_id(
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
) -> str:

    for key in (
        "file_path",
        "source_path",
        "document_path",
        "path",
    ):

        value = row.get(key)

        if value:
            return str(value)

    return ""


def locate_exact(
    rows: list[dict[str, Any]],
    *,
    runtime_id: int,
    expected_path: str,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        if result_id(row) == runtime_id:
            return rank

        if (
            expected_path
            and result_path(row)
            == expected_path
        ):
            return rank

    return None


def locate_family(
    rows: list[dict[str, Any]],
    family: set[int],
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        rid = result_id(
            row
        )

        if (
            rid is not None
            and rid in family
        ):
            return rank

    return None


# ============================================================
# SHADOW SEARCH MATRIX
# ============================================================

def search_matrix(
    *,
    query: str,
    runtime_id: int,
    expected_path: str,
    family: set[int],
    db_path: Path,
    search_catalog: Any,
) -> dict[str, Any]:

    variants = query_variants(
        query
    )

    matrix = []

    best_exact = None
    best_family = None

    best_exact_variant = None
    best_exact_horizon = None

    best_family_variant = None
    best_family_horizon = None

    for variant in variants:

        for horizon in HORIZONS:

            rows = list(
                search_catalog(
                    variant,
                    db_path=db_path,
                    limit=horizon,
                )
            )

            exact_rank = locate_exact(
                rows,
                runtime_id=
                    runtime_id,
                expected_path=
                    expected_path,
            )

            family_rank = locate_family(
                rows,
                family,
            )

            matrix.append(
                {
                    "variant":
                        variant,

                    "horizon":
                        horizon,

                    "returned":
                        len(rows),

                    "exact_rank":
                        exact_rank,

                    "family_rank":
                        family_rank,
                }
            )

            if (
                exact_rank is not None
                and (
                    best_exact is None
                    or exact_rank
                    < best_exact
                )
            ):

                best_exact = exact_rank
                best_exact_variant = (
                    variant
                )
                best_exact_horizon = (
                    horizon
                )

            if (
                family_rank is not None
                and (
                    best_family is None
                    or family_rank
                    < best_family
                )
            ):

                best_family = family_rank
                best_family_variant = (
                    variant
                )
                best_family_horizon = (
                    horizon
                )

    return {
        "variants":
            variants,

        "matrix":
            matrix,

        "best_exact_rank":
            best_exact,

        "best_exact_variant":
            best_exact_variant,

        "best_exact_horizon":
            best_exact_horizon,

        "best_family_rank":
            best_family,

        "best_family_variant":
            best_family_variant,

        "best_family_horizon":
            best_family_horizon,
    }


# ============================================================
# RECOVERY CLASSIFICATION
# ============================================================

def classify_recovery(
    *,
    original_query: str,
    shadow: dict[str, Any],
) -> str:

    exact_rank = shadow.get(
        "best_exact_rank"
    )

    exact_variant = shadow.get(
        "best_exact_variant"
    )

    exact_horizon = shadow.get(
        "best_exact_horizon"
    )

    family_rank = shadow.get(
        "best_family_rank"
    )

    family_variant = shadow.get(
        "best_family_variant"
    )

    family_horizon = shadow.get(
        "best_family_horizon"
    )

    normalized_exact = bool(
        exact_variant
        and exact_variant.casefold()
        != original_query.casefold()
    )

    normalized_family = bool(
        family_variant
        and family_variant.casefold()
        != original_query.casefold()
    )

    if exact_rank is not None:

        if (
            normalized_exact
            and exact_horizon == 25
        ):
            return (
                "RECOVERED_BY_NORMALIZATION"
            )

        if (
            normalized_exact
            and exact_horizon is not None
            and exact_horizon > 25
        ):
            return (
                "RECOVERED_BY_NORMALIZATION_AND_HORIZON"
            )

        if (
            exact_horizon is not None
            and exact_horizon > 25
        ):
            return (
                "RECOVERED_BY_HORIZON"
            )

        return (
            "RECOVERED_AT_BASELINE"
        )

    if family_rank is not None:

        if (
            normalized_family
            and family_horizon == 25
        ):
            return (
                "RECOVERED_IDENTITY_BY_NORMALIZATION"
            )

        if (
            normalized_family
            and family_horizon is not None
            and family_horizon > 25
        ):
            return (
                "RECOVERED_IDENTITY_BY_NORMALIZATION_AND_HORIZON"
            )

        if (
            family_horizon is not None
            and family_horizon > 25
        ):
            return (
                "RECOVERED_IDENTITY_BY_HORIZON"
            )

        return (
            "RECOVERED_BY_IDENTITY_FAMILY"
        )

    return "NOT_RECOVERED"


# ============================================================
# HORIZON CURVE
# ============================================================

def recovered_at_horizon(
    results: list[dict[str, Any]],
    horizon: int,
) -> int:

    count = 0

    for item in results:

        recovered = False

        for row in item.get(
            "matrix",
            []
        ):

            if row["horizon"] != horizon:
                continue

            if (
                row.get(
                    "exact_rank"
                )
                is not None
                or row.get(
                    "family_rank"
                )
                is not None
            ):

                recovered = True
                break

        if recovered:
            count += 1

    return count


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
        "--r1g-report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--report",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--tsv",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    from core.knowledge_catalog.search import (
        search_catalog,
    )

    started = time.monotonic()

    r1g = json.loads(
        args.r1g_report.read_text(
            encoding="utf-8"
        )
    )

    failures = list(
        r1g.get(
            "failures",
            []
        )
    )

    con = ro(
        args.db
    )

    try:

        print(
            "============================================================"
        )
        print(
            " GENESIS RECALL R1G-R1"
        )
        print(
            " QUERY NORMALIZATION + CANDIDATE HORIZON"
        )
        print(
            " SHADOW CERTIFICATION"
        )
        print(
            "============================================================"
        )

        print()
        print(
            "R1G failure cases:",
            len(failures),
        )

        # ====================================================
        # 1. FAILURE RECOVERY MATRIX
        # ====================================================

        print()
        print(
            "=== 1. FAILURE RECOVERY MATRIX ==="
        )

        results = []

        recovery_counts = Counter()

        for index, item in enumerate(
            failures,
            start=1,
        ):

            runtime_id = int(
                item["runtime_id"]
            )

            query = str(
                item["query"]
            )

            original_class = str(
                item["classification"]
            )

            doc = runtime_document(
                con,
                runtime_id,
            )

            if doc is None:

                record = {
                    "runtime_id":
                        runtime_id,

                    "query":
                        query,

                    "original_class":
                        original_class,

                    "recovery":
                        "RUNTIME_DOCUMENT_MISSING",

                    "matrix":
                        [],
                }

                results.append(
                    record
                )

                recovery_counts[
                    record[
                        "recovery"
                    ]
                ] += 1

                continue

            family = identity_family(
                con,
                str(
                    doc["sha256"]
                ),
            )

            shadow = search_matrix(
                query=query,
                runtime_id=
                    runtime_id,
                expected_path=str(
                    doc[
                        "file_path"
                    ]
                ),
                family=family,
                db_path=args.db,
                search_catalog=
                    search_catalog,
            )

            recovery = classify_recovery(
                original_query=query,
                shadow=shadow,
            )

            recovery_counts[
                recovery
            ] += 1

            record = {
                "runtime_id":
                    runtime_id,

                "title":
                    doc[
                        "title"
                    ],

                "query":
                    query,

                "normalized_query":
                    normalize_query(
                        query
                    ),

                "relaxed_query":
                    relaxed_query(
                        query
                    ),

                "original_class":
                    original_class,

                "identity_family":
                    sorted(
                        family
                    ),

                "best_exact_rank":
                    shadow[
                        "best_exact_rank"
                    ],

                "best_exact_variant":
                    shadow[
                        "best_exact_variant"
                    ],

                "best_exact_horizon":
                    shadow[
                        "best_exact_horizon"
                    ],

                "best_family_rank":
                    shadow[
                        "best_family_rank"
                    ],

                "best_family_variant":
                    shadow[
                        "best_family_variant"
                    ],

                "best_family_horizon":
                    shadow[
                        "best_family_horizon"
                    ],

                "recovery":
                    recovery,

                "variants":
                    shadow[
                        "variants"
                    ],

                "matrix":
                    shadow[
                        "matrix"
                    ],
            }

            results.append(
                record
            )

            print()
            print(
                "------------------------------------------------------------"
            )

            print(
                f"[{index:02d}/{len(failures):02d}] "
                f"id={runtime_id}"
            )

            print(
                "title          :",
                doc["title"],
            )

            print(
                "original query :",
                query,
            )

            print(
                "normalized     :",
                record[
                    "normalized_query"
                ],
            )

            print(
                "relaxed        :",
                record[
                    "relaxed_query"
                ],
            )

            print(
                "original class :",
                original_class,
            )

            print(
                "exact rank     :",
                record[
                    "best_exact_rank"
                ],
            )

            print(
                "exact horizon  :",
                record[
                    "best_exact_horizon"
                ],
            )

            print(
                "family rank    :",
                record[
                    "best_family_rank"
                ],
            )

            print(
                "family horizon :",
                record[
                    "best_family_horizon"
                ],
            )

            print(
                "best exact var :",
                record[
                    "best_exact_variant"
                ],
            )

            print(
                "RECOVERY       :",
                recovery,
            )

        # ====================================================
        # 2. RECOVERY COUNTS
        # ====================================================

        recovered = sum(
            1
            for item in results
            if item.get(
                "recovery"
            )
            not in {
                "NOT_RECOVERED",
                "RUNTIME_DOCUMENT_MISSING",
            }
        )

        total = len(
            results
        )

        recovery_pct = (
            recovered
            * 100.0
            / total
            if total
            else 0.0
        )

        print()
        print(
            "=== 2. RECOVERY MECHANISMS ==="
        )

        for name, count in (
            recovery_counts.most_common()
        ):

            print(
                f"{name:48} : {count}"
            )

        # ====================================================
        # 3. HORIZON CURVE
        # ====================================================

        print()
        print(
            "=== 3. HORIZON RECOVERY CURVE ==="
        )

        horizon_curve = {}

        for horizon in HORIZONS:

            count = (
                recovered_at_horizon(
                    results,
                    horizon,
                )
            )

            horizon_curve[
                str(
                    horizon
                )
            ] = count

            print(
                f"horizon {horizon:>3} : "
                f"{count}/{total}"
            )

        # ====================================================
        # 4. KNOWN SEMANTIC REGRESSION
        # ====================================================

        print()
        print(
            "=== 4. KNOWN SEMANTIC REGRESSION ==="
        )

        semantic_results = []

        semantic_pass = True

        for spec in KNOWN:

            doc = runtime_document(
                con,
                spec[
                    "runtime_id"
                ],
            )

            if doc is None:

                semantic_results.append(
                    {
                        **spec,
                        "pass":
                            False,
                        "reason":
                            "runtime_document_missing",
                    }
                )

                semantic_pass = False
                continue

            best_rank = None
            best_variant = None

            for variant in query_variants(
                spec["query"]
            ):

                rows = list(
                    search_catalog(
                        variant,
                        db_path=args.db,
                        limit=100,
                    )
                )

                rank = locate_exact(
                    rows,
                    runtime_id=
                        spec[
                            "runtime_id"
                        ],
                    expected_path=str(
                        doc[
                            "file_path"
                        ]
                    ),
                )

                if (
                    rank is not None
                    and (
                        best_rank is None
                        or rank < best_rank
                    )
                ):

                    best_rank = rank
                    best_variant = variant

            passed = (
                best_rank is not None
                and best_rank <= 5
            )

            semantic_pass = (
                semantic_pass
                and passed
            )

            semantic_results.append(
                {
                    **spec,
                    "best_rank":
                        best_rank,

                    "best_variant":
                        best_variant,

                    "pass":
                        passed,
                }
            )

            print(
                f"{spec['name']:24} "
                f"rank={str(best_rank):<4} "
                f"PASS={passed}"
            )

        # ====================================================
        # 5. ADVERSARIAL CONTROLS
        # ====================================================

        print()
        print(
            "=== 5. ADVERSARIAL CONTROLS ==="
        )

        adversarial_results = []

        suspicious_adversarial = 0

        for query in NEGATIVE:

            variants = (
                query_variants(
                    query
                )
            )

            max_results = 0

            for variant in variants:

                rows = list(
                    search_catalog(
                        variant,
                        db_path=args.db,
                        limit=100,
                    )
                )

                max_results = max(
                    max_results,
                    len(rows),
                )

            suspicious = (
                max_results >= 100
            )

            if suspicious:
                suspicious_adversarial += 1

            adversarial_results.append(
                {
                    "query":
                        query,

                    "variants":
                        variants,

                    "max_results":
                        max_results,

                    "suspicious":
                        suspicious,
                }
            )

            print()
            print(
                "query:",
                query,
            )

            print(
                "  max results :",
                max_results,
            )

            print(
                "  suspicious  :",
                suspicious,
            )

        # ====================================================
        # 6. CERTIFICATION
        #
        # IMPORTANT:
        # Recovery percentage is an experimental result.
        # It is NOT a certification threshold.
        # ====================================================

        shadow_certified = (
            total == 22
            and semantic_pass
            and suspicious_adversarial == 0
        )

        elapsed = (
            time.monotonic()
            - started
        )

        print()
        print(
            "============================================================"
        )

        print(
            " R1G-R1 SHADOW CERTIFICATION RESULT"
        )

        print(
            "============================================================"
        )

        print(
            "failures tested       :",
            total,
        )

        print(
            "failures recovered    :",
            f"{recovered}/{total}",
        )

        print(
            "recovery percentage   :",
            f"{recovery_pct:.1f}%",
        )

        print()
        print(
            "semantic regression   :",
            "PASS"
            if semantic_pass
            else "FAIL",
        )

        print(
            "adversarial issues    :",
            suspicious_adversarial,
        )

        print()
        print(
            "SHADOW CERTIFIED      :",
            shadow_certified,
        )

        print()
        print(
            "NOTE:"
        )

        print(
            "Recovery percentage is diagnostic only."
        )

        print(
            "Certification means the experiment completed"
        )

        print(
            "against all 22 failures without semantic or"
        )

        print(
            "adversarial regression."
        )

        print()
        print(
            f"elapsed seconds       : "
            f"{elapsed:.2f}"
        )

        print(
            "production DB writes  : 0"
        )

        print(
            "production source edits: 0"
        )

        print(
            "============================================================"
        )

        report = {
            "schema":
                SCHEMA,

            "read_only":
                True,

            "failures_tested":
                total,

            "failures_recovered":
                recovered,

            "recovery_percentage":
                recovery_pct,

            "recovery_counts":
                dict(
                    recovery_counts
                ),

            "horizon_curve":
                horizon_curve,

            "failure_results":
                results,

            "semantic_results":
                semantic_results,

            "semantic_pass":
                semantic_pass,

            "adversarial_results":
                adversarial_results,

            "suspicious_adversarial":
                suspicious_adversarial,

            "shadow_certified":
                shadow_certified,

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

        with args.tsv.open(
            "w",
            encoding="utf-8",
            newline="",
        ) as handle:

            fields = (
                "runtime_id",
                "original_class",
                "recovery",
                "best_exact_rank",
                "best_exact_horizon",
                "best_family_rank",
                "best_family_horizon",
                "query",
                "normalized_query",
                "relaxed_query",
                "best_exact_variant",
                "title",
            )

            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
                delimiter="\t",
            )

            writer.writeheader()

            for item in results:

                writer.writerow(
                    {
                        key:
                            item.get(
                                key
                            )
                        for key in fields
                    }
                )

        return (
            0
            if shadow_certified
            else 1
        )

    finally:

        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
