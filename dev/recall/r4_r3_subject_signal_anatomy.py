from __future__ import annotations

import csv
import inspect
import json
import math
import re
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

R4_R2_DETAIL = (
    OUTDIR
    / "r4_r2_qualification_drop_detail.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r3_subject_signal_anatomy.json"
)

DETAIL_TSV = (
    OUTDIR
    / "r4_r3_subject_signal_detail.tsv"
)

CONTROL_TSV = (
    OUTDIR
    / "r4_r3_subject_control_detail.tsv"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r3_subject_source_map.txt"
)

QUALIFIED_SOURCE = (
    PROJECT
    / "core"
    / "knowledge_catalog"
    / "qualified_search.py"
)

EVALUATOR_SOURCE = (
    PROJECT
    / "core"
    / "retrieval"
    / "qualification"
    / "evaluator.py"
)


SUBJECT_SAMPLE_SIZE = 24
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
# GENERIC ACCESS
# ============================================================

def get_value(
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


def as_text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(value)


def as_float(
    value: Any,
) -> float | None:

    if value is None:
        return None

    try:
        return float(
            value
        )
    except Exception:
        return None


def as_int(
    value: Any,
) -> int | None:

    if value is None:
        return None

    try:
        return int(
            value
        )
    except Exception:
        return None


# ============================================================
# DOCUMENT IDENTITY
# ============================================================

def candidate_document_id(
    candidate: Any,
) -> int | None:

    metadata = get_value(
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

    return as_int(
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

        parsed = as_int(
            get_value(
                row,
                name,
            )
        )

        if parsed is not None:
            return parsed

    metadata = get_value(
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

            parsed = as_int(
                raw_row.get(
                    "document_id"
                )
            )

            if parsed is not None:
                return parsed

    return None


# ============================================================
# EVIDENCE ACCESS
# ============================================================

def evidence_candidate(
    evidence: Any,
) -> Any:

    return get_value(
        evidence,
        "candidate",
    )


def score_value(
    evidence: Any,
    name: str,
) -> float | None:

    score = get_value(
        evidence,
        "score",
    )

    return as_float(
        get_value(
            score,
            name,
        )
    )


def evidence_decision(
    evidence: Any,
) -> str:

    return as_text(
        get_value(
            evidence,
            "decision",
        )
    )


def evidence_explanation(
    evidence: Any,
) -> str:

    return as_text(
        get_value(
            evidence,
            "explanation",
        )
    )


def find_target_evidence(
    result: Any,
    target_document_id: int,
):

    matches = []

    for bucket_name in (
        "accepted",
        "rejected",
    ):

        bucket = list(
            get_value(
                result,
                bucket_name,
            )
            or ()
        )

        for index, evidence in enumerate(
            bucket
        ):

            candidate = (
                evidence_candidate(
                    evidence
                )
            )

            if (
                candidate_document_id(
                    candidate
                )
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
# RAW-ROW / CANDIDATE FIELD ANATOMY
# ============================================================

def raw_row_from_candidate(
    candidate: Any,
) -> Mapping[str, Any]:

    metadata = get_value(
        candidate,
        "metadata",
    )

    if not isinstance(
        metadata,
        Mapping,
    ):
        return {}

    raw_row = metadata.get(
        "raw_row"
    )

    if not isinstance(
        raw_row,
        Mapping,
    ):
        return {}

    return raw_row


def candidate_field(
    candidate: Any,
    name: str,
) -> Any:

    return get_value(
        candidate,
        name,
    )


def raw_field(
    candidate: Any,
    name: str,
) -> Any:

    return raw_row_from_candidate(
        candidate
    ).get(
        name
    )


def normalized_tokens(
    value: Any,
) -> tuple[str, ...]:

    text = (
        as_text(
            value
        )
        .lower()
    )

    return tuple(
        re.findall(
            r"[a-z0-9]+",
            text,
        )
    )


def token_overlap(
    query: str,
    value: Any,
) -> float | None:

    query_tokens = set(
        normalized_tokens(
            query
        )
    )

    value_tokens = set(
        normalized_tokens(
            value
        )
    )

    if not query_tokens:
        return None

    return (
        len(
            query_tokens
            & value_tokens
        )
        / len(
            query_tokens
        )
    )


def field_state(
    value: Any,
) -> str:

    if value is None:
        return "NONE"

    text = as_text(
        value
    ).strip()

    if not text:
        return "EMPTY"

    return "POPULATED"


# ============================================================
# DETERMINISTIC SAMPLE
# ============================================================

def deterministic_sample(
    rows: list[dict[str, str]],
    count: int,
):

    if len(rows) < count:
        raise RuntimeError(
            "insufficient subject-drop population"
        )

    if count == 1:
        return [
            rows[
                len(rows)
                // 2
            ]
        ]

    indexes = []

    for index in range(
        count
    ):

        position = (
            index
            * (
                len(rows)
                - 1
            )
            / (
                count
                - 1
            )
        )

        indexes.append(
            round(
                position
            )
        )

    # Quantile indexes are unique because 221 >> 24.
    if (
        len(
            set(
                indexes
            )
        )
        != count
    ):

        raise RuntimeError(
            "deterministic sample indexes collided"
        )

    return [
        rows[index]
        for index in indexes
    ]


# ============================================================
# SOURCE MAP
# ============================================================

def source_fragments(
    path: Path,
    patterns: tuple[str, ...],
    radius: int = 5,
) -> str:

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    relevant = set()

    for index, line in enumerate(
        lines
    ):

        lower = line.lower()

        if any(
            pattern.lower()
            in lower
            for pattern
            in patterns
        ):

            start = max(
                0,
                index - radius,
            )

            end = min(
                len(lines),
                index + radius + 1,
            )

            for line_index in range(
                start,
                end
            ):
                relevant.add(
                    line_index
                )

    output = []

    previous = None

    for index in sorted(
        relevant
    ):

        if (
            previous is not None
            and index
            > previous + 1
        ):
            output.append(
                "..."
            )

        output.append(
            f"{index + 1:05d}: "
            + lines[index]
        )

        previous = index

    return "\n".join(
        output
    )


# ============================================================
# LOAD R4-R2 SUBJECT POPULATION
# ============================================================

with R4_R2_DETAIL.open(
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


subject_rows = [
    row
    for row in rows
    if (
        row.get(
            "failure_class"
        )
        == "SUBJECT"
    )
]


if len(subject_rows) != 221:

    raise RuntimeError(
        f"Expected 221 SUBJECT failures, "
        f"found {len(subject_rows)}"
    )


sample = deterministic_sample(
    subject_rows,
    SUBJECT_SAMPLE_SIZE,
)


# ============================================================
# SOURCE PROVENANCE CAPTURE
# ============================================================

source_map = []

source_map.append(
    "=" * 78
)

source_map.append(
    "QUALIFIED_SEARCH.PY — SUBJECT-RELATED SOURCE"
)

source_map.append(
    "=" * 78
)

source_map.append(
    source_fragments(
        QUALIFIED_SOURCE,
        (
            "subject",
            "EvidenceCandidate",
            "candidate=",
            "QualificationCandidate",
        ),
        radius=6,
    )
)


source_map.append("")
source_map.append(
    "=" * 78
)

source_map.append(
    "EVALUATOR.PY — SUBJECT-RELATED SOURCE"
)

source_map.append(
    "=" * 78
)

source_map.append(
    source_fragments(
        EVALUATOR_SOURCE,
        (
            "subject",
            "minimum_subject",
            "subject_score",
            "subject_similarity",
            "rejected_subject",
        ),
        radius=8,
    )
)


SOURCE_MAP.write_text(
    "\n".join(
        source_map
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# SUBJECT-DROP SAMPLE TRACE
# ============================================================

started = time.time()

records = []

candidate_subject_state = Counter()
raw_subject_state = Counter()
raw_title_state = Counter()
subject_equals_title = Counter()


print("=" * 78)
print(" GENESIS RECALL R4-R3")
print(" SUBJECT SIGNAL PROVENANCE + ZERO-SCORE ANATOMY")
print("=" * 78)

print()
print("=== A. SUBJECT FAILURE POPULATION ===")

print(
    "total SUBJECT failures:",
    len(
        subject_rows
    ),
)

print(
    "deterministic sample     :",
    len(
        sample
    ),
)


print()
print("=== B. 24-DOCUMENT SUBJECT SIGNAL TRACE ===")


for sample_index, row in enumerate(
    sample,
    start=1,
):

    document_id = int(
        row[
            "document_id"
        ]
    )

    query = row[
        "query"
    ]

    raw_rows = search_catalog(
        query,
        db_path=DB,
        limit=RAW_LIMIT,
    )

    qualified_rows, result = (
        qs.qualify_rows(
            query,
            raw_rows,
        )
    )

    matches = find_target_evidence(
        result,
        document_id,
    )

    if not matches:

        raise RuntimeError(
            f"target evidence missing "
            f"for document {document_id}"
        )


    # Prefer rejected evidence because these are known drops.
    selected = None

    for match in matches:

        if match[0] == "rejected":
            selected = match
            break

    if selected is None:
        selected = matches[0]


    bucket, evidence_index, evidence = (
        selected
    )

    candidate = evidence_candidate(
        evidence
    )

    raw_row = raw_row_from_candidate(
        candidate
    )


    candidate_title = candidate_field(
        candidate,
        "title",
    )

    candidate_subject = candidate_field(
        candidate,
        "subject",
    )

    candidate_source_path = candidate_field(
        candidate,
        "source_path",
    )


    raw_title = raw_row.get(
        "title"
    )

    raw_subject = raw_row.get(
        "subject"
    )

    raw_name = raw_row.get(
        "name"
    )

    raw_path = (
        raw_row.get(
            "source_path"
        )
        or raw_row.get(
            "path"
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

    subject_score = score_value(
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


    candidate_subject_state[
        field_state(
            candidate_subject
        )
    ] += 1

    raw_subject_state[
        field_state(
            raw_subject
        )
    ] += 1

    raw_title_state[
        field_state(
            raw_title
        )
    ] += 1


    if (
        as_text(
            candidate_subject
        ).strip()
        ==
        as_text(
            candidate_title
        ).strip()
        and
        as_text(
            candidate_subject
        ).strip()
    ):
        subject_equals_title[
            "YES"
        ] += 1
    else:
        subject_equals_title[
            "NO"
        ] += 1


    record = {
        "sample_index":
            sample_index,

        "document_id":
            document_id,

        "query":
            query,

        "bucket":
            bucket,

        "evidence_index":
            evidence_index,

        "decision":
            evidence_decision(
                evidence
            ),

        "explanation":
            evidence_explanation(
                evidence
            ),

        "candidate_title":
            candidate_title,

        "candidate_subject":
            candidate_subject,

        "candidate_source_path":
            candidate_source_path,

        "candidate_subject_state":
            field_state(
                candidate_subject
            ),

        "raw_title":
            raw_title,

        "raw_subject":
            raw_subject,

        "raw_name":
            raw_name,

        "raw_path":
            raw_path,

        "raw_subject_state":
            field_state(
                raw_subject
            ),

        "query_title_overlap":
            token_overlap(
                query,
                candidate_title,
            ),

        "query_subject_overlap":
            token_overlap(
                query,
                candidate_subject,
            ),

        "query_raw_title_overlap":
            token_overlap(
                query,
                raw_title,
            ),

        "query_raw_subject_overlap":
            token_overlap(
                query,
                raw_subject,
            ),

        "subject_equals_title":
            (
                as_text(
                    candidate_subject
                ).strip()
                ==
                as_text(
                    candidate_title
                ).strip()
                and
                bool(
                    as_text(
                        candidate_subject
                    ).strip()
                )
            ),

        "lexical":
            lexical,

        "entity":
            entity,

        "subject_score":
            subject_score,

        "phrase":
            phrase,

        "provenance":
            provenance,

        "final":
            final,
    }


    records.append(
        record
    )


    print()
    print(
        f"[{sample_index:02d}/"
        f"{SUBJECT_SAMPLE_SIZE:02d}] "
        f"document_id={document_id}"
    )

    print(
        "  query              :",
        query,
    )

    print(
        "  candidate.title    :",
        candidate_title,
    )

    print(
        "  candidate.subject  :",
        repr(
            candidate_subject
        ),
    )

    print(
        "  raw_row.title      :",
        repr(
            raw_title
        ),
    )

    print(
        "  raw_row.subject    :",
        repr(
            raw_subject
        ),
    )

    print(
        "  raw_row.name       :",
        repr(
            raw_name
        ),
    )

    print(
        "  query/title overlap:",
        record[
            "query_title_overlap"
        ],
    )

    print(
        "  query/subject ovlp :",
        record[
            "query_subject_overlap"
        ],
    )

    print(
        "  lexical            :",
        lexical,
    )

    print(
        "  subject score      :",
        subject_score,
    )

    print(
        "  final              :",
        final,
    )

    print(
        "  decision           :",
        record[
            "decision"
        ],
    )


# ============================================================
# ACCEPTED CONTROLS
# ============================================================

print()
print("=== C. KNOWN-GOOD ACCEPTED CONTROLS ===")


CONTROLS = (
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
        "lane",
        "Edward William Lane Arabic English Lexicon Vol 6",
        86876,
    ),
)


control_records = []


for (
    name,
    query,
    document_id,
) in CONTROLS:

    raw_rows = search_catalog(
        query,
        db_path=DB,
        limit=RAW_LIMIT,
    )

    qualified_rows, result = (
        qs.qualify_rows(
            query,
            raw_rows,
        )
    )

    matches = find_target_evidence(
        result,
        document_id,
    )


    print()
    print(name)

    print(
        "  target document_id:",
        document_id,
    )

    print(
        "  evidence matches  :",
        len(
            matches
        ),
    )


    for match_index, (
        bucket,
        evidence_index,
        evidence,
    ) in enumerate(
        matches,
        start=1,
    ):

        candidate = (
            evidence_candidate(
                evidence
            )
        )

        raw_row = (
            raw_row_from_candidate(
                candidate
            )
        )

        control = {
            "control":
                name,

            "query":
                query,

            "document_id":
                document_id,

            "match_index":
                match_index,

            "bucket":
                bucket,

            "candidate_title":
                candidate_field(
                    candidate,
                    "title",
                ),

            "candidate_subject":
                candidate_field(
                    candidate,
                    "subject",
                ),

            "raw_title":
                raw_row.get(
                    "title"
                ),

            "raw_subject":
                raw_row.get(
                    "subject"
                ),

            "query_title_overlap":
                token_overlap(
                    query,
                    candidate_field(
                        candidate,
                        "title",
                    ),
                ),

            "query_subject_overlap":
                token_overlap(
                    query,
                    candidate_field(
                        candidate,
                        "subject",
                    ),
                ),

            "decision":
                evidence_decision(
                    evidence
                ),

            "explanation":
                evidence_explanation(
                    evidence
                ),

            "lexical":
                score_value(
                    evidence,
                    "lexical",
                ),

            "entity":
                score_value(
                    evidence,
                    "entity",
                ),

            "subject_score":
                score_value(
                    evidence,
                    "subject",
                ),

            "phrase":
                score_value(
                    evidence,
                    "phrase",
                ),

            "provenance":
                score_value(
                    evidence,
                    "provenance",
                ),

            "final":
                score_value(
                    evidence,
                    "final",
                ),
        }


        control_records.append(
            control
        )


        print(
            "  bucket             :",
            bucket,
        )

        print(
            "  candidate.subject  :",
            repr(
                control[
                    "candidate_subject"
                ]
            ),
        )

        print(
            "  raw_row.subject    :",
            repr(
                control[
                    "raw_subject"
                ]
            ),
        )

        print(
            "  lexical            :",
            control[
                "lexical"
            ],
        )

        print(
            "  subject score      :",
            control[
                "subject_score"
            ],
        )

        print(
            "  final              :",
            control[
                "final"
            ],
        )

        print(
            "  decision           :",
            control[
                "decision"
            ],
        )


# ============================================================
# SOURCE-CONSTRUCTION ANALYSIS
# ============================================================

print()
print("=== D. SUBJECT FIELD POPULATION SUMMARY ===")

print(
    "candidate.subject states:",
    dict(
        candidate_subject_state
    ),
)

print(
    "raw_row.subject states   :",
    dict(
        raw_subject_state
    ),
)

print(
    "raw_row.title states     :",
    dict(
        raw_title_state
    ),
)

print(
    "subject == title         :",
    dict(
        subject_equals_title
    ),
)


# ============================================================
# SIMPLE HYPOTHESIS CLASSIFICATION
# ============================================================

all_candidate_subject_missing = all(
    record[
        "candidate_subject_state"
    ]
    in (
        "NONE",
        "EMPTY",
    )
    for record
    in records
)


all_raw_subject_missing = all(
    record[
        "raw_subject_state"
    ]
    in (
        "NONE",
        "EMPTY",
    )
    for record
    in records
)


all_subject_scores_zero = all(
    record[
        "subject_score"
    ]
    == 0.0
    for record
    in records
)


title_overlap_present = sum(
    1
    for record
    in records
    if (
        record[
            "query_title_overlap"
        ]
        is not None
        and
        record[
            "query_title_overlap"
        ]
        > 0.0
    )
)


subject_overlap_present = sum(
    1
    for record
    in records
    if (
        record[
            "query_subject_overlap"
        ]
        is not None
        and
        record[
            "query_subject_overlap"
        ]
        > 0.0
    )
)


if (
    all_candidate_subject_missing
    and all_raw_subject_missing
):

    dominant_hypothesis = (
        "SUBJECT_METADATA_ABSENT"
    )

elif (
    all_candidate_subject_missing
    and not all_raw_subject_missing
):

    dominant_hypothesis = (
        "SUBJECT_NOT_PROPAGATED_TO_CANDIDATE"
    )

elif (
    not all_candidate_subject_missing
    and all_subject_scores_zero
):

    dominant_hypothesis = (
        "SUBJECT_SCORING_OR_NORMALIZATION_DEFECT"
    )

else:

    dominant_hypothesis = (
        "MIXED_SUBJECT_SIGNAL_FAILURE"
    )


# ============================================================
# WRITE DETAIL TSV
# ============================================================

detail_fields = [
    "sample_index",
    "document_id",
    "query",
    "bucket",
    "evidence_index",
    "decision",
    "explanation",
    "candidate_title",
    "candidate_subject",
    "candidate_source_path",
    "candidate_subject_state",
    "raw_title",
    "raw_subject",
    "raw_name",
    "raw_path",
    "raw_subject_state",
    "query_title_overlap",
    "query_subject_overlap",
    "query_raw_title_overlap",
    "query_raw_subject_overlap",
    "subject_equals_title",
    "lexical",
    "entity",
    "subject_score",
    "phrase",
    "provenance",
    "final",
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

    writer.writerows(
        records
    )


# ============================================================
# WRITE CONTROL TSV
# ============================================================

control_fields = [
    "control",
    "query",
    "document_id",
    "match_index",
    "bucket",
    "candidate_title",
    "candidate_subject",
    "raw_title",
    "raw_subject",
    "query_title_overlap",
    "query_subject_overlap",
    "decision",
    "explanation",
    "lexical",
    "entity",
    "subject_score",
    "phrase",
    "provenance",
    "final",
]


with CONTROL_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=control_fields,
        delimiter="\t",
    )

    writer.writeheader()

    writer.writerows(
        control_records
    )


# ============================================================
# JSON REPORT
# ============================================================

elapsed = (
    time.time()
    - started
)


payload = {
    "genesis_recall":
        "R4-R3",

    "purpose":
        (
            "Subject Signal Provenance "
            "+ Zero-Score Anatomy"
        ),

    "population": {
        "subject_failures":
            len(
                subject_rows
            ),

        "sample_size":
            len(
                records
            ),

        "sample_method":
            "deterministic_quantile",
    },

    "subject_field_states": {
        "candidate_subject":
            dict(
                candidate_subject_state
            ),

        "raw_subject":
            dict(
                raw_subject_state
            ),

        "raw_title":
            dict(
                raw_title_state
            ),

        "subject_equals_title":
            dict(
                subject_equals_title
            ),
    },

    "signal_summary": {
        "all_candidate_subject_missing":
            all_candidate_subject_missing,

        "all_raw_subject_missing":
            all_raw_subject_missing,

        "all_subject_scores_zero":
            all_subject_scores_zero,

        "title_overlap_present":
            title_overlap_present,

        "subject_overlap_present":
            subject_overlap_present,

        "dominant_hypothesis":
            dominant_hypothesis,
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

    "records":
        records,

    "accepted_controls":
        control_records,

    "source_map":
        str(
            SOURCE_MAP
        ),

    "elapsed_seconds":
        round(
            elapsed,
            3,
        ),
}


REPORT.write_text(
    json.dumps(
        payload,
        indent=2,
        sort_keys=True,
        default=str,
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 78)
print(" GENESIS RECALL R4-R3 RESULT")
print("=" * 78)


print()
print("SUBJECT FAILURE POPULATION")

print(
    "  total subject failures       :",
    len(
        subject_rows
    ),
)

print(
    "  deterministic trace sample   :",
    len(
        records
    ),
)


print()
print("SUBJECT SIGNAL PROVENANCE")

print(
    "  candidate.subject states     :",
    dict(
        candidate_subject_state
    ),
)

print(
    "  raw_row.subject states       :",
    dict(
        raw_subject_state
    ),
)

print(
    "  raw_row.title states         :",
    dict(
        raw_title_state
    ),
)

print(
    "  subject equals title         :",
    dict(
        subject_equals_title
    ),
)


print()
print("ZERO-SCORE ANATOMY")

print(
    "  all candidate subject absent :",
    all_candidate_subject_missing,
)

print(
    "  all raw subject absent       :",
    all_raw_subject_missing,
)

print(
    "  all subject scores zero      :",
    all_subject_scores_zero,
)

print(
    "  query/title overlap > 0      :",
    f"{title_overlap_present}/{len(records)}",
)

print(
    "  query/subject overlap > 0    :",
    f"{subject_overlap_present}/{len(records)}",
)


print()
print("DOMINANT HYPOTHESIS")

print(
    " ",
    dominant_hypothesis,
)


print()
print("ACCEPTED CONTROL OBSERVATIONS")

accepted_control_count = sum(
    1
    for record
    in control_records
    if record[
        "bucket"
    ]
    == "accepted"
)

zero_subject_controls = sum(
    1
    for record
    in control_records
    if record[
        "subject_score"
    ]
    == 0.0
)

positive_subject_controls = sum(
    1
    for record
    in control_records
    if (
        record[
            "subject_score"
        ]
        is not None
        and record[
            "subject_score"
        ]
        > 0.0
    )
)


print(
    "  accepted control evidence    :",
    accepted_control_count,
)

print(
    "  controls with subject=0      :",
    zero_subject_controls,
)

print(
    "  controls with subject>0      :",
    positive_subject_controls,
)


print()
print("CERTIFICATION")

complete = (
    len(
        records
    )
    == SUBJECT_SAMPLE_SIZE
    and all_subject_scores_zero
)


print(
    "  exact sample                 :",
    len(
        records
    )
    == SUBJECT_SAMPLE_SIZE,
)

print(
    "  zero-score reproduced        :",
    all_subject_scores_zero,
)

print(
    "  source map captured          :",
    SOURCE_MAP.exists()
    and SOURCE_MAP.stat().st_size
    > 0,
)

print()
print(
    "R4-R3 DIAGNOSTIC CERTIFIED    :",
    complete,
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
    "control TSV:",
    CONTROL_TSV,
)

print(
    "source map :",
    SOURCE_MAP,
)

print()
print(
    "elapsed seconds:",
    round(
        elapsed,
        2,
    )
)

print("=" * 78)


raise SystemExit(
    0
    if complete
    else 1
)
