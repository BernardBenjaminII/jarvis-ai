from __future__ import annotations

import json
import time

from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

REPORT = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r2_production_catalog_awareness.json"
)


CATALOG_CANARIES = (
    (
        "list_sora",
        "List Sora names",
        69550,
    ),
    (
        "riyadh_saliheem",
        "Riyadh us Saliheem",
        84923,
    ),
    (
        "la_ta7zan",
        "la ta7zan",
        86912,
    ),
    (
        "kameez_pattern",
        "kameez pattern",
        86958,
    ),
    (
        "guerilla_warfare",
        "Guevara Che Guerilla Warfare",
        89199,
    ),
    (
        "lane_lexicon",
        "Edward William Lane Arabic English Lexicon Vol 6",
        86876,
    ),
)


SEMANTIC_CANARIES = (
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
    (
        "civil_defense",
        "civil defense manual",
        18,
    ),
    (
        "army_survival",
        "US Army survival manual",
        32,
    ),
    (
        "electronics",
        "practical electronics handbook",
        42,
    ),
    (
        "marx",
        "Marx mathematical manuscripts",
        89330,
    ),
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


def result_id(
    row: dict[str, Any],
) -> int | None:

    for key in (
        "runtime_document_id",
        "document_id",
        "runtime_id",
        "doc_id",
        "id",
    ):

        value = row.get(
            key
        )

        if value is None:
            continue

        try:
            return int(
                value
            )
        except Exception:
            pass

    return None


def locate(
    rows: list[dict[str, Any]],
    runtime_id: int,
) -> int | None:

    for rank, row in enumerate(
        rows,
        start=1,
    ):

        if result_id(
            row
        ) == runtime_id:
            return rank

    return None


def main() -> int:

    from core.knowledge_catalog.catalog_awareness import (
        search_document_identity,
    )

    from core.knowledge_catalog.search import (
        search_catalog,
    )

    from core.knowledge_catalog.qualified_search import (
        search_qualified_catalog,
    )

    started = time.monotonic()

    report: dict[str, Any] = {
        "catalog_canaries": [],
        "semantic_canaries": [],
        "negative_controls": [],
    }


    print(
        "=" * 72
    )

    print(
        " GENESIS RECALL R2"
    )

    print(
        " PRODUCTION CATALOG AWARENESS CERTIFICATION"
    )

    print(
        "=" * 72
    )


    # ========================================================
    # A. DIRECT CATALOG IDENTITY
    # ========================================================

    print()
    print(
        "=== A. DIRECT CATALOG IDENTITY ==="
    )

    direct_pass = True

    for name, query, target in (
        CATALOG_CANARIES
    ):

        rows = list(
            search_document_identity(
                query,
                db_path=DB,
                limit=12,
            )
        )

        rank = locate(
            rows,
            target,
        )

        passed = bool(
            rank is not None
            and rank <= 5
        )

        direct_pass = (
            direct_pass
            and passed
        )

        print(
            f"{name:24} "
            f"rank={str(rank):<4} "
            f"PASS={passed}"
        )

        report[
            "catalog_canaries"
        ].append(
            {
                "name":
                    name,

                "query":
                    query,

                "runtime_id":
                    target,

                "identity_rank":
                    rank,

                "identity_pass":
                    passed,
            }
        )


    # ========================================================
    # B. PRODUCTION RAW RETRIEVAL
    # ========================================================

    print()
    print(
        "=== B. PRODUCTION RAW RETRIEVAL ==="
    )

    raw_pass = True

    for item in report[
        "catalog_canaries"
    ]:

        rows = list(
            search_catalog(
                item["query"],
                db_path=DB,
                limit=25,
            )
        )

        rank = locate(
            rows,
            item[
                "runtime_id"
            ],
        )

        passed = bool(
            rank is not None
            and rank <= 5
        )

        raw_pass = (
            raw_pass
            and passed
        )

        item[
            "raw_rank"
        ] = rank

        item[
            "raw_pass"
        ] = passed

        print(
            f"{item['name']:24} "
            f"rank={str(rank):<4} "
            f"PASS={passed}"
        )


    # ========================================================
    # C. PRODUCTION QUALIFIED RETRIEVAL
    #
    # This is the important end-to-end retrieval path:
    #
    # catalog awareness
    #       ->
    # search_catalog()
    #       ->
    # qualification / R1F rescue
    #       ->
    # grounding candidates
    # ========================================================

    print()
    print(
        "=== C. END-TO-END PRODUCTION QUALIFIED RETRIEVAL ==="
    )

    qualified_pass = True

    for item in report[
        "catalog_canaries"
    ]:

        rows = list(
            search_qualified_catalog(
                item["query"],
                db_path=DB,
                limit=25,
            )
        )

        rank = locate(
            rows,
            item[
                "runtime_id"
            ],
        )

        passed = bool(
            rank is not None
            and rank <= 5
        )

        qualified_pass = (
            qualified_pass
            and passed
        )

        item[
            "qualified_rank"
        ] = rank

        item[
            "qualified_pass"
        ] = passed

        matching = None

        if rank is not None:
            matching = rows[
                rank - 1
            ]

        item[
            "qualification_decision"
        ] = (
            matching.get(
                "qualification_decision"
            )
            if matching
            else None
        )

        item[
            "retrieval_channel"
        ] = (
            matching.get(
                "retrieval_channel"
            )
            if matching
            else None
        )

        print(
            f"{item['name']:24} "
            f"rank={str(rank):<4} "
            f"PASS={passed}"
        )


    # ========================================================
    # D. EXISTING SEMANTIC REGRESSION
    # ========================================================

    print()
    print(
        "=== D. EXISTING SEMANTIC REGRESSION ==="
    )

    semantic_pass = True

    for name, query, target in (
        SEMANTIC_CANARIES
    ):

        raw_rows = list(
            search_catalog(
                query,
                db_path=DB,
                limit=25,
            )
        )

        qualified_rows = list(
            search_qualified_catalog(
                query,
                db_path=DB,
                limit=25,
            )
        )

        raw_rank = locate(
            raw_rows,
            target,
        )

        qualified_rank = locate(
            qualified_rows,
            target,
        )

        passed = bool(
            qualified_rank
            is not None
            and qualified_rank <= 5
        )

        semantic_pass = (
            semantic_pass
            and passed
        )

        report[
            "semantic_canaries"
        ].append(
            {
                "name":
                    name,

                "query":
                    query,

                "runtime_id":
                    target,

                "raw_rank":
                    raw_rank,

                "qualified_rank":
                    qualified_rank,

                "pass":
                    passed,
            }
        )

        print(
            f"{name:24} "
            f"raw={str(raw_rank):<4} "
            f"qualified={str(qualified_rank):<4} "
            f"PASS={passed}"
        )


    # ========================================================
    # E. ADVERSARIAL IDENTITY PRECISION
    # ========================================================

    print()
    print(
        "=== E. ADVERSARIAL IDENTITY PRECISION ==="
    )

    negative_pass = True

    for query in NEGATIVE:

        identity_rows = list(
            search_document_identity(
                query,
                db_path=DB,
                limit=12,
            )
        )

        identity_hits = len(
            identity_rows
        )

        passed = (
            identity_hits == 0
        )

        negative_pass = (
            negative_pass
            and passed
        )

        report[
            "negative_controls"
        ].append(
            {
                "query":
                    query,

                "identity_hits":
                    identity_hits,

                "pass":
                    passed,
            }
        )

        print()
        print(
            "query:",
            query,
        )

        print(
            "  identity hits:",
            identity_hits,
        )

        print(
            "  PASS:",
            passed,
        )


    # ========================================================
    # F. CERTIFICATION
    # ========================================================

    certified = bool(
        direct_pass
        and raw_pass
        and qualified_pass
        and semantic_pass
        and negative_pass
    )

    elapsed = (
        time.monotonic()
        - started
    )

    report.update(
        {
            "direct_identity_pass":
                direct_pass,

            "raw_retrieval_pass":
                raw_pass,

            "qualified_retrieval_pass":
                qualified_pass,

            "semantic_regression_pass":
                semantic_pass,

            "adversarial_identity_pass":
                negative_pass,

            "certified":
                certified,

            "elapsed_seconds":
                elapsed,
        }
    )

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
    print(
        "=" * 72
    )

    print(
        " GENESIS RECALL R2 PRODUCTION RESULT"
    )

    print(
        "=" * 72
    )

    print(
        "direct identity          :",
        "PASS"
        if direct_pass
        else "FAIL",
    )

    print(
        "raw retrieval integration:",
        "PASS"
        if raw_pass
        else "FAIL",
    )

    print(
        "qualified retrieval      :",
        "PASS"
        if qualified_pass
        else "FAIL",
    )

    print(
        "semantic regression      :",
        "PASS"
        if semantic_pass
        else "FAIL",
    )

    print(
        "adversarial identity     :",
        "PASS"
        if negative_pass
        else "FAIL",
    )

    print()

    print(
        "R2 CERTIFIED             :",
        certified,
    )

    print(
        "elapsed seconds          :",
        f"{elapsed:.2f}",
    )

    print(
        "=" * 72
    )

    return (
        0
        if certified
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
