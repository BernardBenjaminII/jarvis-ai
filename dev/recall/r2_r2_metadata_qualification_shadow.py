from __future__ import annotations

import csv
import json
import sqlite3
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
    / "r2_r2_metadata_qualification_shadow.json"
)

TSV = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
    / "r2_r2_metadata_qualification_shadow.tsv"
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


def open_ro() -> sqlite3.Connection:

    con = sqlite3.connect(
        f"file:{DB.resolve()}?mode=ro",
        uri=True,
    )

    con.row_factory = sqlite3.Row

    con.execute(
        "PRAGMA query_only=ON"
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


def best_chunk(
    con: sqlite3.Connection,
    runtime_id: int,
) -> dict[str, Any] | None:

    row = con.execute(
        """
        SELECT
            document_id,
            chunk_id,
            chunk_text,
            title,
            file_path
        FROM runtime_chunks_fts
        WHERE CAST(document_id AS INTEGER)=?
        ORDER BY CAST(chunk_id AS INTEGER)
        LIMIT 1
        """,
        (runtime_id,),
    ).fetchone()

    return (
        dict(row)
        if row is not None
        else None
    )


def build_candidate(
    *,
    doc: dict[str, Any],
    chunk: dict[str, Any],
    preserve_subject: bool,
) -> dict[str, Any]:

    runtime_id = int(
        doc["id"]
    )

    title = str(
        doc["title"]
        or ""
    )

    path = str(
        doc["file_path"]
        or ""
    )

    text = str(
        chunk["chunk_text"]
        or ""
    )

    subject = (
        title
        if preserve_subject
        else ""
    )

    return {
        "id":
            runtime_id,

        "document_id":
            runtime_id,

        "runtime_document_id":
            runtime_id,

        "runtime_id":
            runtime_id,

        "title":
            title,

        # THIS is the repair under test.
        "subject":
            subject,

        "file_path":
            path,

        "source_path":
            path,

        "path":
            path,

        "media_type":
            doc.get(
                "media_type"
            ),

        "chunk_id":
            chunk.get(
                "chunk_id"
            ),

        "chunk_text":
            text,

        "content_text":
            text,

        "content":
            text,

        "text":
            text,

        "excerpt":
            text,

        "retrieval_score":
            0.99,

        "score":
            0.99,

        "confidence":
            0.99,

        "identity_score":
            0.99,

        "identity_exact":
            False,

        "identity_phrase":
            True,

        "identity_coverage":
            1.0,

        "retrieval_channel":
            "catalog_identity",

        "source_kind":
            "runtime_catalog",

        "source_type":
            "runtime_catalog",

        "assigned_by":
            "genesis_recall_r2_r2_shadow",
    }


def qualification_snapshot(
    query: str,
    candidate: dict[str, Any],
) -> dict[str, Any]:

    from core.knowledge_catalog.qualified_search import (
        qualify_rows,
    )

    from core.retrieval.qualification.evaluator import (
        QualificationEngine,
    )

    qualified, result = qualify_rows(
        query,
        [candidate],
        engine=QualificationEngine(),
    )

    rejected = getattr(
        result,
        "rejected",
        (),
    )

    accepted = getattr(
        result,
        "accepted",
        (),
    )

    evidence = None

    if accepted:
        evidence = accepted[0]

    elif rejected:
        evidence = rejected[0]

    decision = (
        getattr(
            evidence,
            "decision",
            None,
        )
        if evidence
        else None
    )

    explanation = (
        getattr(
            evidence,
            "explanation",
            None,
        )
        if evidence
        else None
    )

    score = (
        getattr(
            evidence,
            "score",
            None,
        )
        if evidence
        else None
    )

    evidence_candidate = (
        getattr(
            evidence,
            "candidate",
            None,
        )
        if evidence
        else None
    )

    return {
        "accepted":
            bool(
                qualified
            ),

        "qualified_count":
            len(
                qualified
            ),

        "decision":
            (
                getattr(
                    decision,
                    "value",
                    str(decision),
                )
                if decision is not None
                else None
            ),

        "explanation":
            explanation,

        "lexical":
            getattr(
                score,
                "lexical",
                None,
            )
            if score
            else None,

        "phrase":
            getattr(
                score,
                "phrase",
                None,
            )
            if score
            else None,

        "entity":
            getattr(
                score,
                "entity",
                None,
            )
            if score
            else None,

        "subject_score":
            getattr(
                score,
                "subject",
                None,
            )
            if score
            else None,

        "provenance":
            getattr(
                score,
                "provenance",
                None,
            )
            if score
            else None,

        "final":
            getattr(
                score,
                "final",
                None,
            )
            if score
            else None,

        "evidence_subject":
            getattr(
                evidence_candidate,
                "subject",
                None,
            )
            if evidence_candidate
            else None,

        "evidence_title":
            getattr(
                evidence_candidate,
                "title",
                None,
            )
            if evidence_candidate
            else None,
    }


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

    started = time.monotonic()

    con = open_ro()

    report: dict[str, Any] = {
        "catalog_canaries":
            [],

        "semantic_canaries":
            [],

        "negative_controls":
            [],
    }

    print(
        "=" * 72
    )

    print(
        " GENESIS RECALL R2-R2"
    )

    print(
        " CATALOG IDENTITY METADATA PRESERVATION"
    )

    print(
        " + QUALIFICATION SHADOW CERTIFICATION"
    )

    print(
        "=" * 72
    )


    # ========================================================
    # A. BASELINE VS METADATA-PRESERVED CATALOG CANARIES
    # ========================================================

    print()
    print(
        "=== A. CATALOG IDENTITY QUALIFICATION MATRIX ==="
    )

    catalog_pass = True

    lane_fixed = False

    for (
        name,
        query,
        runtime_id,
    ) in CATALOG_CANARIES:

        doc = runtime_document(
            con,
            runtime_id,
        )

        chunk = best_chunk(
            con,
            runtime_id,
        )

        if (
            doc is None
            or chunk is None
        ):

            print(
                name,
                ": MISSING RUNTIME MATERIALIZATION",
            )

            catalog_pass = False
            continue

        baseline_candidate = (
            build_candidate(
                doc=doc,
                chunk=chunk,
                preserve_subject=False,
            )
        )

        repaired_candidate = (
            build_candidate(
                doc=doc,
                chunk=chunk,
                preserve_subject=True,
            )
        )

        baseline = (
            qualification_snapshot(
                query,
                baseline_candidate,
            )
        )

        repaired = (
            qualification_snapshot(
                query,
                repaired_candidate,
            )
        )

        preserved = bool(
            repaired[
                "evidence_subject"
            ]
            and repaired[
                "evidence_subject"
            ]
            == doc["title"]
        )

        passed = bool(
            repaired[
                "accepted"
            ]
            and preserved
        )

        if name == "lane_lexicon":

            lane_fixed = bool(
                baseline[
                    "accepted"
                ]
                is False
                and repaired[
                    "accepted"
                ]
                is True
                and preserved
            )

        catalog_pass = (
            catalog_pass
            and passed
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
                    runtime_id,

                "title":
                    doc[
                        "title"
                    ],

                "baseline":
                    baseline,

                "repaired":
                    repaired,

                "subject_preserved":
                    preserved,

                "pass":
                    passed,
            }
        )

        print()
        print(
            f"{name:24}"
        )

        print(
            "  baseline decision :",
            baseline[
                "decision"
            ],
        )

        print(
            "  baseline subject  :",
            baseline[
                "evidence_subject"
            ],
        )

        print(
            "  baseline subjscore:",
            baseline[
                "subject_score"
            ],
        )

        print(
            "  repaired decision :",
            repaired[
                "decision"
            ],
        )

        print(
            "  repaired subject  :",
            repaired[
                "evidence_subject"
            ],
        )

        print(
            "  repaired subjscore:",
            repaired[
                "subject_score"
            ],
        )

        print(
            "  repaired final    :",
            repaired[
                "final"
            ],
        )

        print(
            "  PASS              :",
            passed,
        )


    # ========================================================
    # B. EXISTING PRODUCTION SEMANTIC REGRESSION
    # ========================================================

    print()
    print(
        "=== B. EXISTING SEMANTIC REGRESSION ==="
    )

    from core.knowledge_catalog.search import (
        search_catalog,
    )

    from core.knowledge_catalog.qualified_search import (
        search_qualified_catalog,
    )

    semantic_pass = True

    for (
        name,
        query,
        runtime_id,
    ) in SEMANTIC_CANARIES:

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
            runtime_id,
        )

        qualified_rank = locate(
            qualified_rows,
            runtime_id,
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
                    runtime_id,

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
    # C. ADVERSARIAL SHADOW QUALIFICATION
    # ========================================================

    print()
    print(
        "=== C. ADVERSARIAL METADATA-PRESERVATION CONTROLS ==="
    )

    negative_pass = True

    # Use a real catalog document as the synthetic candidate but
    # preserve its legitimate metadata. Nonsense queries must not
    # qualify simply because subject/title metadata is present.
    control_doc = runtime_document(
        con,
        86876,
    )

    control_chunk = best_chunk(
        con,
        86876,
    )

    if (
        control_doc is None
        or control_chunk is None
    ):

        negative_pass = False

    else:

        for query in NEGATIVE_QUERIES:

            candidate = (
                build_candidate(
                    doc=control_doc,
                    chunk=control_chunk,
                    preserve_subject=True,
                )
            )

            snapshot = (
                qualification_snapshot(
                    query,
                    candidate,
                )
            )

            passed = (
                snapshot[
                    "accepted"
                ]
                is False
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

                    "decision":
                        snapshot[
                            "decision"
                        ],

                    "accepted":
                        snapshot[
                            "accepted"
                        ],

                    "subject_score":
                        snapshot[
                            "subject_score"
                        ],

                    "final":
                        snapshot[
                            "final"
                        ],

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
                "  decision :",
                snapshot[
                    "decision"
                ],
            )

            print(
                "  accepted :",
                snapshot[
                    "accepted"
                ],
            )

            print(
                "  PASS     :",
                passed,
            )


    # ========================================================
    # D. CERTIFICATION
    # ========================================================

    certified = bool(
        len(
            report[
                "catalog_canaries"
            ]
        ) == 6
        and catalog_pass
        and lane_fixed
        and semantic_pass
        and negative_pass
    )

    elapsed = (
        time.monotonic()
        - started
    )

    report.update(
        {
            "catalog_canaries_pass":
                catalog_pass,

            "lane_lexicon_fixed":
                lane_fixed,

            "semantic_regression_pass":
                semantic_pass,

            "adversarial_shadow_pass":
                negative_pass,

            "certified":
                certified,

            "elapsed_seconds":
                elapsed,

            "production_source_changes":
                0,

            "production_db_writes":
                0,
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


    fields = (
        "name",
        "runtime_id",
        "baseline_decision",
        "baseline_subject_score",
        "repaired_decision",
        "repaired_subject_score",
        "repaired_final",
        "subject_preserved",
        "pass",
    )

    with TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:

        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
            delimiter="\t",
        )

        writer.writeheader()

        for item in report[
            "catalog_canaries"
        ]:

            writer.writerow(
                {
                    "name":
                        item[
                            "name"
                        ],

                    "runtime_id":
                        item[
                            "runtime_id"
                        ],

                    "baseline_decision":
                        item[
                            "baseline"
                        ][
                            "decision"
                        ],

                    "baseline_subject_score":
                        item[
                            "baseline"
                        ][
                            "subject_score"
                        ],

                    "repaired_decision":
                        item[
                            "repaired"
                        ][
                            "decision"
                        ],

                    "repaired_subject_score":
                        item[
                            "repaired"
                        ][
                            "subject_score"
                        ],

                    "repaired_final":
                        item[
                            "repaired"
                        ][
                            "final"
                        ],

                    "subject_preserved":
                        item[
                            "subject_preserved"
                        ],

                    "pass":
                        item[
                            "pass"
                        ],
                }
            )


    print()
    print(
        "=" * 72
    )

    print(
        " GENESIS RECALL R2-R2 SHADOW RESULT"
    )

    print(
        "=" * 72
    )

    print(
        "catalog canaries        :",
        "PASS"
        if catalog_pass
        else "FAIL",
    )

    print(
        "Lane qualification fix  :",
        "PASS"
        if lane_fixed
        else "FAIL",
    )

    print(
        "semantic regression     :",
        "PASS"
        if semantic_pass
        else "FAIL",
    )

    print(
        "adversarial shadow      :",
        "PASS"
        if negative_pass
        else "FAIL",
    )

    print()
    print(
        "R2-R2 CERTIFIED         :",
        certified,
    )

    print(
        "elapsed seconds         :",
        f"{elapsed:.2f}",
    )

    print(
        "production source edits : 0"
    )

    print(
        "production DB writes    : 0"
    )

    print(
        "=" * 72
    )

    con.close()

    return (
        0
        if certified
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
