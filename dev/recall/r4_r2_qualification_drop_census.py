from __future__ import annotations

import csv
import json
import math
import sys
import time

from collections import Counter
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

OUTDIR = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
)

R3_FAILURES = (
    OUTDIR
    / "r3_recall_failures.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r2_qualification_drop_census.json"
)

DETAIL_TSV = (
    OUTDIR
    / "r4_r2_qualification_drop_detail.tsv"
)

CLASS_TSV = (
    OUTDIR
    / "r4_r2_failure_class_census.tsv"
)

RESCUE_TSV = (
    OUTDIR
    / "r4_r2_rescue_class_census.tsv"
)

EXPECTED_DROPS = 228

RAW_LIMIT = 100


from core.knowledge_catalog.search import (
    search_catalog,
)

import core.knowledge_catalog.qualified_search as qs

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


ENGINE = QualificationEngine()


# ============================================================
# BASIC OBJECT ACCESS
# ============================================================

def read_value(
    obj: Any,
    name: str,
) -> Any:

    if obj is None:
        return None

    if isinstance(
        obj,
        Mapping,
    ):
        return obj.get(
            name
        )

    try:
        return getattr(
            obj,
            name,
        )
    except Exception:
        return None


def int_value(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:
        return int(value)
    except Exception:
        return None


# ============================================================
# DOCUMENT IDENTITY
# ============================================================

def candidate_document_id(
    candidate: Any,
) -> int | None:
    """
    Production identity contract certified by R7/R4-R8:

        candidate.metadata["raw_row"]["document_id"]
    """

    metadata = read_value(
        candidate,
        "metadata",
    )

    if not isinstance(
        metadata,
        Mapping,
    ):
        return None

    raw_row = metadata.get(
        "raw_row"
    )

    if not isinstance(
        raw_row,
        Mapping,
    ):
        return None

    return int_value(
        raw_row.get(
            "document_id"
        )
    )


def row_document_id(
    row: Any,
) -> int | None:

    for name in (
        "document_id",
        "runtime_document_id",
        "id",
    ):

        value = read_value(
            row,
            name,
        )

        parsed = int_value(
            value
        )

        if parsed is not None:
            return parsed

    metadata = read_value(
        row,
        "metadata",
    )

    if isinstance(
        metadata,
        Mapping,
    ):

        raw_row = metadata.get(
            "raw_row"
        )

        if isinstance(
            raw_row,
            Mapping,
        ):

            parsed = int_value(
                raw_row.get(
                    "document_id"
                )
            )

            if parsed is not None:
                return parsed

    return None


# ============================================================
# R3 DROP POPULATION
# ============================================================

def load_r3_drops():
    with R3_FAILURES.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as handle:

        rows = list(
            csv.DictReader(
                handle,
                delimiter="\t",
            )
        )

    drops = [
        row
        for row in rows
        if row.get(
            "status"
        )
        == "QUALIFICATION_DROP"
    ]

    return drops


# ============================================================
# SCORE / EVIDENCE HELPERS
# ============================================================

def score_value(
    evidence: Any,
    name: str,
) -> float | None:

    score = read_value(
        evidence,
        "score",
    )

    if score is None:
        return None

    value = read_value(
        score,
        name,
    )

    if value is None:
        return None

    try:
        return float(
            value
        )
    except Exception:
        return None


def evidence_decision(
    evidence: Any,
) -> str | None:

    value = read_value(
        evidence,
        "decision",
    )

    if value is None:
        return None

    return str(value)


def evidence_explanation(
    evidence: Any,
) -> str | None:

    value = read_value(
        evidence,
        "explanation",
    )

    if value is None:
        return None

    return str(value)


def evidence_candidate(
    evidence: Any,
) -> Any:

    return read_value(
        evidence,
        "candidate",
    )


# ============================================================
# FIND TARGET EVIDENCE
# ============================================================

def target_evidence(
    result: Any,
    target_document_id: int,
):

    accepted = list(
        read_value(
            result,
            "accepted",
        )
        or ()
    )

    rejected = list(
        read_value(
            result,
            "rejected",
        )
        or ()
    )

    matches = []

    for bucket_name, bucket in (
        (
            "accepted",
            accepted,
        ),
        (
            "rejected",
            rejected,
        ),
    ):

        for index, evidence in enumerate(
            bucket
        ):

            candidate = (
                evidence_candidate(
                    evidence
                )
            )

            document_id = (
                candidate_document_id(
                    candidate
                )
            )

            if (
                document_id
                == target_document_id
            ):

                matches.append(
                    (
                        bucket_name,
                        index,
                        evidence,
                    )
                )

    return matches


# ============================================================
# FAILURE CLASSIFICATION
# ============================================================

def classify_failure(
    decision: str | None,
    explanation: str | None,
    lexical: float | None,
    subject: float | None,
    phrase: float | None,
    provenance: float | None,
    final: float | None,
) -> str:

    text = " ".join(
        value
        for value in (
            decision,
            explanation,
        )
        if value
    ).lower()

    if (
        "confidence" in text
        or "low_confidence" in text
    ):
        return "LOW_CONFIDENCE"

    if "lexical" in text:
        return "LEXICAL"

    if "subject" in text:
        return "SUBJECT"

    if "phrase" in text:
        return "PHRASE"

    if "provenance" in text:
        return "PROVENANCE"

    if (
        lexical is not None
        and lexical
        < float(
            ENGINE.thresholds.minimum_lexical
        )
    ):
        return "LEXICAL"

    if (
        subject is not None
        and subject
        < float(
            ENGINE.thresholds.minimum_subject
        )
    ):
        return "SUBJECT"

    if (
        final is not None
        and final
        < float(
            ENGINE.thresholds.accept
        )
    ):
        return "LOW_CONFIDENCE"

    if (
        provenance is not None
        and provenance <= 0.0
    ):
        return "PROVENANCE"

    return "OTHER"


# ============================================================
# R1F
# ============================================================

def evaluate_r1f(
    query: str,
    evidence: Any,
    result: Any,
):

    threshold = read_value(
        result,
        "threshold",
    )

    try:
        threshold = float(
            threshold
        )
    except Exception:
        threshold = float(
            ENGINE.thresholds.accept
        )

    try:

        rescue, reason = (
            qs._gate_repair_should_rescue(
                query,
                evidence,
                threshold=threshold,
            )
        )

        return (
            bool(rescue),
            str(reason),
        )

    except Exception as exc:

        return (
            False,
            (
                "R1F_ERROR:"
                + type(exc).__name__
            ),
        )


# ============================================================
# R2 EXACT DOCUMENT IDENTITY
# ============================================================

def evaluate_r2(
    query: str,
    evidence: Any,
    result: Any,
):

    try:

        targets = (
            qs._r2_exact_identity_targets(
                query,
                result,
            )
        )

    except Exception as exc:

        return (
            False,
            (
                "R2_TARGET_ERROR:"
                + type(exc).__name__
            ),
            [],
        )


    try:

        rescue, reason = (
            qs._r2_exact_document_identity_should_rescue(
                query,
                evidence,
                target_document_ids=targets,
            )
        )

        return (
            bool(rescue),
            str(reason),
            sorted(
                int(v)
                for v in targets
            ),
        )

    except Exception as exc:

        return (
            False,
            (
                "R2_RESCUE_ERROR:"
                + type(exc).__name__
            ),
            sorted(
                int(v)
                for v in targets
            ),
        )


# ============================================================
# SCORE DISTRIBUTIONS
# ============================================================

def distribution(
    values: list[float],
):

    clean = sorted(
        value
        for value in values
        if (
            value is not None
            and math.isfinite(
                float(value)
            )
        )
    )

    if not clean:

        return {
            "count": 0,
            "min": None,
            "p10": None,
            "p25": None,
            "median": None,
            "p75": None,
            "p90": None,
            "max": None,
        }


    def q(
        fraction: float,
    ):

        if len(clean) == 1:
            return clean[0]

        position = (
            fraction
            * (
                len(clean)
                - 1
            )
        )

        low = int(
            math.floor(
                position
            )
        )

        high = int(
            math.ceil(
                position
            )
        )

        if low == high:
            return clean[low]

        ratio = (
            position
            - low
        )

        return (
            clean[low]
            * (
                1.0
                - ratio
            )
            +
            clean[high]
            * ratio
        )


    return {
        "count":
            len(clean),

        "min":
            clean[0],

        "p10":
            q(0.10),

        "p25":
            q(0.25),

        "median":
            q(0.50),

        "p75":
            q(0.75),

        "p90":
            q(0.90),

        "max":
            clean[-1],
    }


# ============================================================
# MAIN
# ============================================================

started = time.time()

drops = load_r3_drops()

print("=" * 78)
print(" GENESIS RECALL R4-R2")
print(" CORRECTED QUALIFICATION DROP CENSUS")
print("=" * 78)

print()
print(
    "R3 drops loaded:",
    len(drops),
)

if len(drops) != EXPECTED_DROPS:

    raise RuntimeError(
        f"Expected {EXPECTED_DROPS} drops, "
        f"found {len(drops)}"
    )


records = []

failure_counter = Counter()
decision_counter = Counter()
explanation_counter = Counter()
rescue_counter = Counter()

missing_raw = 0
missing_evidence = 0
multiple_target_evidence = 0

score_lists = {
    "lexical": [],
    "entity": [],
    "subject": [],
    "phrase": [],
    "provenance": [],
    "final": [],
}


print()
print(
    "=== 228-DROP EXACT QUALIFICATION TRACE ==="
)


for index, drop in enumerate(
    drops,
    start=1,
):

    target_id = int(
        drop[
            "document_id"
        ]
    )

    query = str(
        drop[
            "query"
        ]
    )

    raw_rows = search_catalog(
        query,
        db_path=DB,
        limit=RAW_LIMIT,
    )

    raw_rank = None

    for rank, row in enumerate(
        raw_rows,
        start=1,
    ):

        if (
            row_document_id(
                row
            )
            == target_id
        ):

            raw_rank = rank
            break


    if raw_rank is None:

        missing_raw += 1

        record = {
            "sample_index":
                index,

            "document_id":
                target_id,

            "query":
                query,

            "raw_rank":
                None,

            "evidence_bucket":
                None,

            "decision":
                None,

            "explanation":
                "RAW_REPRODUCTION_MISS",

            "lexical":
                None,

            "entity":
                None,

            "subject":
                None,

            "phrase":
                None,

            "provenance":
                None,

            "final":
                None,

            "failure_class":
                "RAW_REPRODUCTION_MISS",

            "r1f_rescue":
                False,

            "r1f_reason":
                None,

            "r2_rescue":
                False,

            "r2_reason":
                None,

            "r2_target_ids":
                [],

            "rescue_class":
                "NO_EXISTING_RESCUE",
        }

        records.append(
            record
        )

        failure_counter[
            "RAW_REPRODUCTION_MISS"
        ] += 1

        rescue_counter[
            "NO_EXISTING_RESCUE"
        ] += 1

        print(
            f"[{index:03d}/{len(drops):03d}] "
            f"id={target_id:<7} "
            "RAW_REPRODUCTION_MISS"
        )

        continue


    qualified_rows, result = (
        qs.qualify_rows(
            query,
            raw_rows,
        )
    )


    matches = target_evidence(
        result,
        target_id,
    )


    if not matches:

        missing_evidence += 1

        record = {
            "sample_index":
                index,

            "document_id":
                target_id,

            "query":
                query,

            "raw_rank":
                raw_rank,

            "evidence_bucket":
                None,

            "decision":
                None,

            "explanation":
                "TARGET_EVIDENCE_NOT_FOUND",

            "lexical":
                None,

            "entity":
                None,

            "subject":
                None,

            "phrase":
                None,

            "provenance":
                None,

            "final":
                None,

            "failure_class":
                "TARGET_EVIDENCE_NOT_FOUND",

            "r1f_rescue":
                False,

            "r1f_reason":
                None,

            "r2_rescue":
                False,

            "r2_reason":
                None,

            "r2_target_ids":
                [],

            "rescue_class":
                "NO_EXISTING_RESCUE",
        }

        records.append(
            record
        )

        failure_counter[
            "TARGET_EVIDENCE_NOT_FOUND"
        ] += 1

        rescue_counter[
            "NO_EXISTING_RESCUE"
        ] += 1

        print(
            f"[{index:03d}/{len(drops):03d}] "
            f"id={target_id:<7} "
            "TARGET_EVIDENCE_NOT_FOUND"
        )

        continue


    if len(matches) > 1:
        multiple_target_evidence += 1


    # Analyze the first matching evidence because all matching
    # chunks belong to the same durable document ID.
    bucket, bucket_index, evidence = (
        matches[0]
    )


    decision = (
        evidence_decision(
            evidence
        )
    )

    explanation = (
        evidence_explanation(
            evidence
        )
    )


    lexical = score_value(
        evidence,
        "lexical",
    )

    entity = score_value(
        evidence,
        "entity",
    )

    subject = score_value(
        evidence,
        "subject",
    )

    phrase = score_value(
        evidence,
        "phrase",
    )

    provenance = score_value(
        evidence,
        "provenance",
    )

    final = score_value(
        evidence,
        "final",
    )


    failure_class = (
        classify_failure(
            decision,
            explanation,
            lexical,
            subject,
            phrase,
            provenance,
            final,
        )
    )


    r1f_rescue, r1f_reason = (
        evaluate_r1f(
            query,
            evidence,
            result,
        )
    )


    (
        r2_rescue,
        r2_reason,
        r2_target_ids,
    ) = evaluate_r2(
        query,
        evidence,
        result,
    )


    if (
        r1f_rescue
        and r2_rescue
    ):

        rescue_class = (
            "R1F_AND_R2"
        )

    elif r1f_rescue:

        rescue_class = (
            "R1F_CONTENT_RESCUE"
        )

    elif r2_rescue:

        rescue_class = (
            "R2_IDENTITY_RESCUE"
        )

    else:

        rescue_class = (
            "NO_EXISTING_RESCUE"
        )


    record = {
        "sample_index":
            index,

        "document_id":
            target_id,

        "query":
            query,

        "raw_rank":
            raw_rank,

        "evidence_bucket":
            bucket,

        "evidence_index":
            bucket_index,

        "target_evidence_matches":
            len(matches),

        "decision":
            decision,

        "explanation":
            explanation,

        "lexical":
            lexical,

        "entity":
            entity,

        "subject":
            subject,

        "phrase":
            phrase,

        "provenance":
            provenance,

        "final":
            final,

        "failure_class":
            failure_class,

        "r1f_rescue":
            r1f_rescue,

        "r1f_reason":
            r1f_reason,

        "r2_rescue":
            r2_rescue,

        "r2_reason":
            r2_reason,

        "r2_target_ids":
            ",".join(
                str(v)
                for v
                in r2_target_ids
            ),

        "rescue_class":
            rescue_class,
    }


    records.append(
        record
    )


    failure_counter[
        failure_class
    ] += 1

    decision_counter[
        str(decision)
    ] += 1

    explanation_counter[
        str(explanation)
    ] += 1

    rescue_counter[
        rescue_class
    ] += 1


    for name, value in (
        (
            "lexical",
            lexical,
        ),
        (
            "entity",
            entity,
        ),
        (
            "subject",
            subject,
        ),
        (
            "phrase",
            phrase,
        ),
        (
            "provenance",
            provenance,
        ),
        (
            "final",
            final,
        ),
    ):

        if value is not None:

            score_lists[
                name
            ].append(
                value
            )


    print(
        f"[{index:03d}/{len(drops):03d}] "
        f"id={target_id:<7} "
        f"raw={raw_rank:<4} "
        f"{bucket:<8} "
        f"{failure_class:<20} "
        f"{rescue_class}"
    )


# ============================================================
# AGGREGATE SCORE DISTRIBUTIONS
# ============================================================

score_distributions = {
    name:
        distribution(
            values
        )
    for name, values
    in score_lists.items()
}


# ============================================================
# WRITE DETAIL TSV
# ============================================================

detail_fields = [
    "sample_index",
    "document_id",
    "query",
    "raw_rank",
    "evidence_bucket",
    "evidence_index",
    "target_evidence_matches",
    "decision",
    "explanation",
    "lexical",
    "entity",
    "subject",
    "phrase",
    "provenance",
    "final",
    "failure_class",
    "r1f_rescue",
    "r1f_reason",
    "r2_rescue",
    "r2_reason",
    "r2_target_ids",
    "rescue_class",
]


with DETAIL_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=detail_fields,
        delimiter="\t",
    )

    writer.writeheader()

    for record in records:

        writer.writerow(
            {
                key:
                    record.get(
                        key
                    )
                for key
                in detail_fields
            }
        )


# ============================================================
# FAILURE CLASS TSV
# ============================================================

with CLASS_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=(
            "failure_class",
            "count",
            "pct",
        ),
        delimiter="\t",
    )

    writer.writeheader()

    for name, count in (
        failure_counter.most_common()
    ):

        writer.writerow(
            {
                "failure_class":
                    name,

                "count":
                    count,

                "pct":
                    round(
                        (
                            count
                            / len(records)
                        )
                        * 100.0,
                        4,
                    ),
            }
        )


# ============================================================
# RESCUE CLASS TSV
# ============================================================

with RESCUE_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=(
            "rescue_class",
            "count",
            "pct",
        ),
        delimiter="\t",
    )

    writer.writeheader()

    for name, count in (
        rescue_counter.most_common()
    ):

        writer.writerow(
            {
                "rescue_class":
                    name,

                "count":
                    count,

                "pct":
                    round(
                        (
                            count
                            / len(records)
                        )
                        * 100.0,
                        4,
                    ),
            }
        )


# ============================================================
# COMPLETENESS
# ============================================================

trace_failures = (
    missing_raw
    + missing_evidence
)

anatomized = (
    len(records)
    - trace_failures
)

anatomy_complete = (
    len(records)
    == EXPECTED_DROPS
    and trace_failures
    == 0
)


# ============================================================
# JSON REPORT
# ============================================================

elapsed = (
    time.time()
    - started
)


report = {
    "genesis_recall":
        "R4-R2",

    "purpose":
        (
            "Corrected Qualification Drop "
            "Anatomy + Rescue-Class Census"
        ),

    "input": {
        "expected_drops":
            EXPECTED_DROPS,

        "actual_drops":
            len(records),
    },

    "thresholds": {
        "accept":
            ENGINE.thresholds.accept,

        "minimum_confidence":
            ENGINE.thresholds.minimum_confidence,

        "minimum_lexical":
            ENGINE.thresholds.minimum_lexical,

        "minimum_subject":
            ENGINE.thresholds.minimum_subject,

        "minimum_phrase":
            ENGINE.thresholds.minimum_phrase,
    },

    "anatomy": {
        "anatomized":
            anatomized,

        "raw_reproduction_misses":
            missing_raw,

        "target_evidence_missing":
            missing_evidence,

        "multiple_target_evidence":
            multiple_target_evidence,

        "complete":
            anatomy_complete,
    },

    "failure_classes":
        dict(
            failure_counter
        ),

    "decisions":
        dict(
            decision_counter
        ),

    "explanations":
        dict(
            explanation_counter
        ),

    "rescue_classes":
        dict(
            rescue_counter
        ),

    "score_distributions":
        score_distributions,

    "elapsed_seconds":
        round(
            elapsed,
            3,
        ),

    "records":
        records,
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
# CONSOLE SUMMARY
# ============================================================

print()
print("=" * 78)
print(" GENESIS RECALL R4-R2 RESULT")
print("=" * 78)


print()
print("INPUT")

print(
    "  qualification drops      :",
    len(records),
)


print()
print("ANATOMY")

print(
    "  successfully anatomized  :",
    f"{anatomized}/{len(records)}",
)

print(
    "  raw reproduction misses  :",
    missing_raw,
)

print(
    "  target evidence missing  :",
    missing_evidence,
)

print(
    "  multiple target evidence :",
    multiple_target_evidence,
)


print()
print("FAILURE CLASSES")

for name, count in (
    failure_counter.most_common()
):

    print(
        f"  {name:<28}"
        f"{count:>4} "
        f"({count / len(records) * 100.0:6.2f}%)"
    )


print()
print("QUALIFICATION DECISIONS")

for name, count in (
    decision_counter.most_common()
):

    print(
        f"  {name:<40}"
        f"{count:>4}"
    )


print()
print("TOP EXPLANATIONS")

for name, count in (
    explanation_counter.most_common(
        15
    )
):

    print(
        f"  {name:<55}"
        f"{count:>4}"
    )


print()
print("EXISTING RESCUE CLASSES")

for name, count in (
    rescue_counter.most_common()
):

    print(
        f"  {name:<28}"
        f"{count:>4} "
        f"({count / len(records) * 100.0:6.2f}%)"
    )


print()
print("SCORE DISTRIBUTIONS")

for name in (
    "lexical",
    "entity",
    "subject",
    "phrase",
    "provenance",
    "final",
):

    stats = (
        score_distributions[
            name
        ]
    )

    print()
    print(
        f"  {name}"
    )

    for key in (
        "count",
        "min",
        "p10",
        "p25",
        "median",
        "p75",
        "p90",
        "max",
    ):

        print(
            f"    {key:<8}: "
            f"{stats[key]}"
        )


print()
print("CERTIFICATION")

print(
    "  exact population         :",
    len(records)
    == EXPECTED_DROPS,
)

print(
    "  anatomy complete         :",
    anatomy_complete,
)

print()
print(
    "R4-R2 DIAGNOSTIC CERTIFIED :",
    anatomy_complete,
)


print()
print(
    "elapsed seconds            :",
    round(
        elapsed,
        2,
    )
)

print()
print(
    "JSON report:",
    REPORT,
)

print(
    "detail TSV :",
    DETAIL_TSV,
)

print(
    "class TSV  :",
    CLASS_TSV,
)

print(
    "rescue TSV :",
    RESCUE_TSV,
)

print("=" * 78)


raise SystemExit(
    0
    if anatomy_complete
    else 1
)
