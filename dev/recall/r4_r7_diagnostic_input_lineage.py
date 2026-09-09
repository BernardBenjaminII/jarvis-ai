from __future__ import annotations

import csv
import hashlib
import json
import re
import sys

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

OUTDIR = PROJECT / "artifacts" / "genesis_recall"


R4R2 = OUTDIR / "r4_r2_qualification_drop_detail.tsv"

R4R3_JSON = OUTDIR / "r4_r3_subject_signal_anatomy.json"
R4R3_DETAIL = OUTDIR / "r4_r3_subject_signal_detail.tsv"

R4R4_JSON = OUTDIR / "r4_r4_subject_analyzer_trace.json"
R4R4_TSV = OUTDIR / "r4_r4_subject_analyzer_trace.tsv"

R4R5_JSON = OUTDIR / "r4_r5_lexical_zero_score_anatomy.json"
R4R5_TSV = OUTDIR / "r4_r5_lexical_zero_score_anatomy.tsv"

R4R6_JSON = OUTDIR / "r4_r6_token_divergence_root_cause.json"
R4R6_SAMPLE = OUTDIR / "r4_r6_token_divergence_sample.tsv"
R4R6_POP = OUTDIR / "r4_r6_token_divergence_population.tsv"

R4R6R1_JSON = OUTDIR / "r4_r6_r1_input_reconstruction_parity.json"
R4R6R1_DETAIL = OUTDIR / "r4_r6_r1_input_reconstruction_parity.tsv"
R4R6R1_RECON = OUTDIR / "r4_r6_r1_divergence_reconciliation.tsv"

REPORT = OUTDIR / "r4_r7_diagnostic_input_lineage.json"
DETAIL = OUTDIR / "r4_r7_diagnostic_input_lineage.tsv"
MISMATCH = OUTDIR / "r4_r7_lineage_mismatch_census.tsv"
TRACE = OUTDIR / "r4_r7_24_case_provenance_trace.txt"


EXPECTED_SAMPLE = 24


# ============================================================
# BASIC TSV / VALUE HELPERS
# ============================================================

def read_tsv(path: Path) -> list[dict[str, str]]:

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

        for key in row.keys():

            if key not in seen:
                fields.append(
                    key
                )
                seen.add(
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


def norm(
    value: Any,
) -> str:

    return str(
        value
        or ""
    ).strip()


def norm_case(
    value: Any,
) -> str:

    return norm(
        value
    ).casefold()


def first(
    row: dict[str, Any],
    *names: str,
) -> str:

    lowered = {
        str(key).casefold():
            value
        for key, value
        in row.items()
    }

    for name in names:

        value = lowered.get(
            name.casefold()
        )

        if value not in (
            None,
            "",
        ):

            return str(
                value
            )

    return ""


# ============================================================
# FIELD EXTRACTORS
# ============================================================

def document_id(
    row: dict[str, Any],
) -> str:

    return first(
        row,
        "document_id",
        "runtime_document_id",
        "target_document_id",
        "target_id",
        "source_id",
        "id",
    )


def query_value(
    row: dict[str, Any],
) -> str:

    return first(
        row,
        "query",
        "qualification_query",
        "search_query",
        "input_query",
        "derived_query",
    )


def subject_value(
    row: dict[str, Any],
) -> str:

    return first(
        row,
        "candidate_subject",
        "subject",
        "raw_subject",
        "document_subject",
    )


def title_value(
    row: dict[str, Any],
) -> str:

    return first(
        row,
        "candidate_title",
        "title",
        "raw_title",
        "document_title",
    )


def candidate_text_value(
    row: dict[str, Any],
) -> str:

    explicit = first(
        row,
        "candidate_text",
        "combined",
        "combined_subject",
    )

    if explicit:
        return explicit

    subject = subject_value(
        row
    )

    title = title_value(
        row
    )

    return " ".join(
        x
        for x in (
            subject,
            title,
        )
        if x
    )


def name_value(
    row: dict[str, Any],
) -> str:

    return first(
        row,
        "name",
        "control",
        "case",
        "sample_name",
    )


# ============================================================
# ARTIFACT SIGNATURES
# ============================================================

def text_signature(
    query: str,
    subject: str,
    title: str,
    candidate_text: str,
) -> str:

    payload = "\x1f".join(
        (
            norm(query),
            norm(subject),
            norm(title),
            norm(candidate_text),
        )
    )

    return hashlib.sha256(
        payload.encode(
            "utf-8",
            "replace",
        )
    ).hexdigest()


def token_signature(
    value: str,
) -> str:

    tokens = tuple(
        re.findall(
            r"[A-Za-z0-9]+",
            norm(value).casefold(),
        )
    )

    return "|".join(
        tokens
    )


# ============================================================
# LOAD ALL ARTIFACTS
# ============================================================

r4r2 = read_tsv(
    R4R2
)

r4r3 = read_tsv(
    R4R3_DETAIL
)

r4r4 = read_tsv(
    R4R4_TSV
)

r4r5 = read_tsv(
    R4R5_TSV
)

r4r6_sample = read_tsv(
    R4R6_SAMPLE
)

r4r6_population = read_tsv(
    R4R6_POP
)

r4r6r1 = read_tsv(
    R4R6R1_DETAIL
)

r4r6r1_recon = read_tsv(
    R4R6R1_RECON
)


# ============================================================
# REDUCE R4-R5 TO ONE CASE PER FAILURE
#
# Keep SUBJECT_PLUS_TITLE only because this is the form R4-R6
# used for its sample reconstruction.
# ============================================================

r4r5_cases = [
    row
    for row in r4r5
    if (
        norm_case(
            first(
                row,
                "category",
            )
        )
        == "failure"
        and
        norm_case(
            first(
                row,
                "form",
            )
        )
        == "subject_plus_title"
    )
]


if len(
    r4r5_cases
) != EXPECTED_SAMPLE:

    raise RuntimeError(
        "expected 24 R4-R5 SUBJECT_PLUS_TITLE "
        f"cases, found {len(r4r5_cases)}"
    )


# ============================================================
# GENERIC INDEXES
# ============================================================

def indexes(
    rows: list[dict[str, Any]],
):

    by_id = defaultdict(
        list
    )

    by_query = defaultdict(
        list
    )

    by_name = defaultdict(
        list
    )

    by_signature = defaultdict(
        list
    )

    for row in rows:

        rid = norm_case(
            document_id(
                row
            )
        )

        query = norm_case(
            query_value(
                row
            )
        )

        name = norm_case(
            name_value(
                row
            )
        )

        sig = text_signature(
            query_value(row),
            subject_value(row),
            title_value(row),
            candidate_text_value(row),
        )

        if rid:
            by_id[
                rid
            ].append(
                row
            )

        if query:
            by_query[
                query
            ].append(
                row
            )

        if name:
            by_name[
                name
            ].append(
                row
            )

        by_signature[
            sig
        ].append(
            row
        )

    return {
        "id":
            by_id,

        "query":
            by_query,

        "name":
            by_name,

        "signature":
            by_signature,
    }


INDEXES = {
    "R4-R2":
        indexes(
            r4r2
        ),

    "R4-R3":
        indexes(
            r4r3
        ),

    "R4-R4":
        indexes(
            r4r4
        ),

    "R4-R5":
        indexes(
            r4r5_cases
        ),

    "R4-R6_SAMPLE":
        indexes(
            r4r6_sample
        ),

    "R4-R6_POP":
        indexes(
            r4r6_population
        ),

    "R4-R6-R1":
        indexes(
            r4r6r1
        ),
}


# ============================================================
# ROW MATCHING
# ============================================================

def choose_match(
    source_row: dict[str, Any],
    target_name: str,
):

    target_index = INDEXES[
        target_name
    ]

    rid = norm_case(
        document_id(
            source_row
        )
    )

    query = norm_case(
        query_value(
            source_row
        )
    )

    name = norm_case(
        name_value(
            source_row
        )
    )

    sig = text_signature(
        query_value(
            source_row
        ),
        subject_value(
            source_row
        ),
        title_value(
            source_row
        ),
        candidate_text_value(
            source_row
        ),
    )


    # --------------------------------------------------------
    # Exact artifact signature is strongest.
    # --------------------------------------------------------

    choices = target_index[
        "signature"
    ].get(
        sig,
        [],
    )

    if len(
        choices
    ) == 1:

        return (
            choices[0],
            "EXACT_SIGNATURE",
            1,
        )


    # --------------------------------------------------------
    # Durable document ID.
    # --------------------------------------------------------

    if rid:

        choices = target_index[
            "id"
        ].get(
            rid,
            [],
        )

        if len(
            choices
        ) == 1:

            return (
                choices[0],
                "DOCUMENT_ID",
                1,
            )

        if len(
            choices
        ) > 1:

            qmatches = [
                row
                for row
                in choices
                if norm_case(
                    query_value(
                        row
                    )
                )
                == query
            ]

            if len(
                qmatches
            ) == 1:

                return (
                    qmatches[0],
                    "DOCUMENT_ID+QUERY",
                    1,
                )


    # --------------------------------------------------------
    # Exact query.
    # --------------------------------------------------------

    if query:

        choices = target_index[
            "query"
        ].get(
            query,
            [],
        )

        if len(
            choices
        ) == 1:

            return (
                choices[0],
                "QUERY",
                1,
            )


    # --------------------------------------------------------
    # Diagnostic sample name.
    # --------------------------------------------------------

    if name:

        choices = target_index[
            "name"
        ].get(
            name,
            [],
        )

        if len(
            choices
        ) == 1:

            return (
                choices[0],
                "NAME",
                1,
            )


    return (
        None,
        "UNMATCHED",
        0,
    )


# ============================================================
# FIELD COMPARISON
# ============================================================

def compare_field(
    left: str,
    right: str,
) -> bool:

    return norm(
        left
    ) == norm(
        right
    )


def comparison(
    canonical: dict[str, Any],
    row: dict[str, Any] | None,
):

    if row is None:

        return {
            "matched":
                False,

            "query_equal":
                False,

            "subject_equal":
                False,

            "title_equal":
                False,

            "candidate_equal":
                False,

            "query_token_equal":
                False,

            "subject_token_equal":
                False,

            "title_token_equal":
                False,
        }


    cq = query_value(
        canonical
    )

    cs = subject_value(
        canonical
    )

    ct = title_value(
        canonical
    )

    cc = candidate_text_value(
        canonical
    )


    rq = query_value(
        row
    )

    rs = subject_value(
        row
    )

    rt = title_value(
        row
    )

    rc = candidate_text_value(
        row
    )


    return {
        "matched":
            True,

        "query_equal":
            compare_field(
                cq,
                rq,
            ),

        "subject_equal":
            compare_field(
                cs,
                rs,
            ),

        "title_equal":
            compare_field(
                ct,
                rt,
            ),

        "candidate_equal":
            compare_field(
                cc,
                rc,
            ),

        "query_token_equal":
            token_signature(
                cq
            )
            ==
            token_signature(
                rq
            ),

        "subject_token_equal":
            token_signature(
                cs
            )
            ==
            token_signature(
                rs
            ),

        "title_token_equal":
            token_signature(
                ct
            )
            ==
            token_signature(
                rt
            ),
    }


# ============================================================
# USE R4-R5 AS THE 24-CASE DIAGNOSTIC POPULATION
#
# Then trace each case backward/forward across artifacts.
# ============================================================

case_records = []

mismatch_counter = Counter()

artifact_match_counter = Counter()

trace_lines = []


trace_lines.append(
    "=" * 78
)

trace_lines.append(
    " GENESIS RECALL R4-R7"
)

trace_lines.append(
    " 24-CASE PROVENANCE TRACE"
)

trace_lines.append(
    "=" * 78
)


ARTIFACT_ORDER = (
    "R4-R2",
    "R4-R3",
    "R4-R4",
    "R4-R5",
    "R4-R6_SAMPLE",
    "R4-R6_POP",
    "R4-R6-R1",
)


for ordinal, r4r5_case in enumerate(
    r4r5_cases,
    start=1,
):

    name = name_value(
        r4r5_case
    )

    canonical_query = query_value(
        r4r5_case
    )

    canonical_subject = subject_value(
        r4r5_case
    )

    canonical_title = title_value(
        r4r5_case
    )

    canonical_candidate = candidate_text_value(
        r4r5_case
    )


    matches = {}

    for artifact in ARTIFACT_ORDER:

        if artifact == "R4-R5":

            matches[
                artifact
            ] = (
                r4r5_case,
                "SELF",
                1,
            )

        else:

            matches[
                artifact
            ] = choose_match(
                r4r5_case,
                artifact,
            )


    # --------------------------------------------------------
    # Prefer R4-R2 as source-of-truth canonical evidence if
    # a corresponding row exists.
    # --------------------------------------------------------

    r4r2_row = matches[
        "R4-R2"
    ][0]

    if r4r2_row is not None:

        source_truth = r4r2_row
        truth_artifact = "R4-R2"

    else:

        source_truth = r4r5_case
        truth_artifact = "R4-R5_FALLBACK"


    truth_query = query_value(
        source_truth
    )

    truth_subject = subject_value(
        source_truth
    )

    truth_title = title_value(
        source_truth
    )

    truth_candidate = candidate_text_value(
        source_truth
    )

    truth_id = document_id(
        source_truth
    )


    artifact_comparisons = {}

    first_divergence = None


    for artifact in ARTIFACT_ORDER:

        row, method, count = matches[
            artifact
        ]

        cmp = comparison(
            source_truth,
            row,
        )

        artifact_comparisons[
            artifact
        ] = {
            **cmp,
            "match_method":
                method,

            "match_count":
                count,

            "document_id":
                (
                    document_id(row)
                    if row
                    else ""
                ),

            "query":
                (
                    query_value(row)
                    if row
                    else ""
                ),

            "subject":
                (
                    subject_value(row)
                    if row
                    else ""
                ),

            "title":
                (
                    title_value(row)
                    if row
                    else ""
                ),

            "candidate_text":
                (
                    candidate_text_value(row)
                    if row
                    else ""
                ),
        }


        if cmp[
            "matched"
        ]:

            artifact_match_counter[
                artifact
            ] += 1


        mismatch_fields = []

        for field in (
            "query_equal",
            "subject_equal",
            "title_equal",
            "candidate_equal",
        ):

            if (
                cmp[
                    "matched"
                ]
                and
                not cmp[
                    field
                ]
            ):

                mismatch_fields.append(
                    field
                )

                mismatch_counter[
                    f"{artifact}:{field}"
                ] += 1


        if (
            cmp[
                "matched"
            ]
            and
            mismatch_fields
            and
            first_divergence is None
        ):

            first_divergence = {
                "artifact":
                    artifact,

                "fields":
                    mismatch_fields,
            }


    if first_divergence is None:

        first_divergence = {
            "artifact":
                "NONE",

            "fields":
                [],
        }


    case_record = {
        "ordinal":
            ordinal,

        "diagnostic_name":
            name,

        "truth_artifact":
            truth_artifact,

        "document_id":
            truth_id,

        "truth_query":
            truth_query,

        "truth_subject":
            truth_subject,

        "truth_title":
            truth_title,

        "truth_candidate":
            truth_candidate,

        "r4r5_query":
            canonical_query,

        "r4r5_subject":
            canonical_subject,

        "r4r5_title":
            canonical_title,

        "r4r5_candidate":
            canonical_candidate,

        "first_divergence_artifact":
            first_divergence[
                "artifact"
            ],

        "first_divergence_fields":
            ",".join(
                first_divergence[
                    "fields"
                ]
            ),

        "artifacts":
            artifact_comparisons,
    }


    case_records.append(
        case_record
    )


    # --------------------------------------------------------
    # Human-readable trace.
    # --------------------------------------------------------

    trace_lines.append("")
    trace_lines.append(
        "-" * 78
    )

    trace_lines.append(
        f"CASE {ordinal:02d}: "
        f"{name}"
    )

    trace_lines.append(
        "-" * 78
    )

    trace_lines.append(
        f"truth artifact : {truth_artifact}"
    )

    trace_lines.append(
        f"document_id    : {truth_id}"
    )

    trace_lines.append(
        f"truth query    : {truth_query}"
    )

    trace_lines.append(
        f"truth subject  : {truth_subject}"
    )

    trace_lines.append(
        f"truth title    : {truth_title}"
    )

    trace_lines.append(
        f"R4-R5 query    : {canonical_query}"
    )

    trace_lines.append(
        f"R4-R5 subject  : {canonical_subject}"
    )

    trace_lines.append(
        f"R4-R5 title    : {canonical_title}"
    )

    trace_lines.append(
        f"first divergence: "
        f"{first_divergence['artifact']} "
        f"{first_divergence['fields']}"
    )

    trace_lines.append("")

    for artifact in ARTIFACT_ORDER:

        data = artifact_comparisons[
            artifact
        ]

        trace_lines.append(
            f"{artifact}"
        )

        trace_lines.append(
            f"  matched      : {data['matched']}"
        )

        trace_lines.append(
            f"  match method : {data['match_method']}"
        )

        trace_lines.append(
            f"  document_id  : {data['document_id']}"
        )

        trace_lines.append(
            f"  query equal  : {data['query_equal']}"
        )

        trace_lines.append(
            f"  subject equal: {data['subject_equal']}"
        )

        trace_lines.append(
            f"  title equal  : {data['title_equal']}"
        )

        trace_lines.append(
            f"  candidate eq : {data['candidate_equal']}"
        )

        trace_lines.append(
            f"  query        : {data['query']}"
        )

        trace_lines.append(
            f"  subject      : {data['subject']}"
        )

        trace_lines.append(
            f"  title        : {data['title']}"
        )


# ============================================================
# DERIVE LINEAGE ROOT CAUSE
# ============================================================

first_divergence_counter = Counter(
    record[
        "first_divergence_artifact"
    ]
    for record
    in case_records
)


if (
    first_divergence_counter.get(
        "R4-R3",
        0,
    )
    == EXPECTED_SAMPLE
):

    lineage_result = (
        "R4R3_DIAGNOSTIC_INPUT_TRANSFORMATION"
    )

elif (
    first_divergence_counter.get(
        "R4-R4",
        0,
    )
    == EXPECTED_SAMPLE
):

    lineage_result = (
        "R4R4_DIAGNOSTIC_INPUT_TRANSFORMATION"
    )

elif (
    first_divergence_counter.get(
        "R4-R5",
        0,
    )
    == EXPECTED_SAMPLE
):

    lineage_result = (
        "R4R5_DIAGNOSTIC_INPUT_TRANSFORMATION"
    )

elif (
    first_divergence_counter.get(
        "R4-R6_SAMPLE",
        0,
    )
    == EXPECTED_SAMPLE
):

    lineage_result = (
        "R4R6_SAMPLE_RECONSTRUCTION_TRANSFORMATION"
    )

elif (
    first_divergence_counter.get(
        "NONE",
        0,
    )
    == EXPECTED_SAMPLE
):

    lineage_result = (
        "NO_TEXT_FIELD_DIVERGENCE_FOUND"
    )

else:

    lineage_result = (
        "MIXED_LINEAGE_DIVERGENCE"
    )


# ============================================================
# WRITE FLAT DETAIL
# ============================================================

flat_rows = []

for record in case_records:

    row = {
        "ordinal":
            record[
                "ordinal"
            ],

        "diagnostic_name":
            record[
                "diagnostic_name"
            ],

        "truth_artifact":
            record[
                "truth_artifact"
            ],

        "document_id":
            record[
                "document_id"
            ],

        "truth_query":
            record[
                "truth_query"
            ],

        "truth_subject":
            record[
                "truth_subject"
            ],

        "truth_title":
            record[
                "truth_title"
            ],

        "r4r5_query":
            record[
                "r4r5_query"
            ],

        "r4r5_subject":
            record[
                "r4r5_subject"
            ],

        "r4r5_title":
            record[
                "r4r5_title"
            ],

        "first_divergence_artifact":
            record[
                "first_divergence_artifact"
            ],

        "first_divergence_fields":
            record[
                "first_divergence_fields"
            ],
    }


    for artifact in ARTIFACT_ORDER:

        data = record[
            "artifacts"
        ][
            artifact
        ]

        prefix = (
            artifact
            .lower()
            .replace(
                "-",
                "_",
            )
        )

        row[
            f"{prefix}_matched"
        ] = data[
            "matched"
        ]

        row[
            f"{prefix}_method"
        ] = data[
            "match_method"
        ]

        row[
            f"{prefix}_query_equal"
        ] = data[
            "query_equal"
        ]

        row[
            f"{prefix}_subject_equal"
        ] = data[
            "subject_equal"
        ]

        row[
            f"{prefix}_title_equal"
        ] = data[
            "title_equal"
        ]

        row[
            f"{prefix}_candidate_equal"
        ] = data[
            "candidate_equal"
        ]


    flat_rows.append(
        row
    )


write_tsv(
    DETAIL,
    flat_rows,
)


# ============================================================
# WRITE MISMATCH CENSUS
# ============================================================

mismatch_rows = []

for key, count in sorted(
    mismatch_counter.items(),
    key=lambda item:
        (
            -item[1],
            item[0],
        ),
):

    artifact, field = key.split(
        ":",
        1,
    )

    mismatch_rows.append(
        {
            "artifact":
                artifact,

            "field":
                field,

            "count":
                count,

            "percent_of_24":
                100.0
                * count
                / EXPECTED_SAMPLE,
        }
    )


write_tsv(
    MISMATCH,
    mismatch_rows,
)


TRACE.write_text(
    "\n".join(
        trace_lines
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# CERTIFICATION
# ============================================================

r4r2_matches = artifact_match_counter.get(
    "R4-R2",
    0,
)

r4r3_matches = artifact_match_counter.get(
    "R4-R3",
    0,
)

r4r4_matches = artifact_match_counter.get(
    "R4-R4",
    0,
)

r4r6_sample_matches = artifact_match_counter.get(
    "R4-R6_SAMPLE",
    0,
)

r4r6_pop_matches = artifact_match_counter.get(
    "R4-R6_POP",
    0,
)

r4r6r1_matches = artifact_match_counter.get(
    "R4-R6-R1",
    0,
)


exact_case_count = (
    len(
        case_records
    )
    == EXPECTED_SAMPLE
)

r4r2_trace_complete = (
    r4r2_matches
    == EXPECTED_SAMPLE
)

r4r3_trace_complete = (
    r4r3_matches
    == EXPECTED_SAMPLE
)

r4r4_trace_complete = (
    r4r4_matches
    == EXPECTED_SAMPLE
)

r4r6_sample_trace_complete = (
    r4r6_sample_matches
    == EXPECTED_SAMPLE
)

r4r6_population_trace_complete = (
    r4r6_pop_matches
    == EXPECTED_SAMPLE
)

r4r6r1_trace_complete = (
    r4r6r1_matches
    == EXPECTED_SAMPLE
)


lineage_complete = all(
    (
        exact_case_count,
        r4r2_trace_complete,
        r4r3_trace_complete,
        r4r4_trace_complete,
        r4r6_sample_trace_complete,
        r4r6_population_trace_complete,
        r4r6r1_trace_complete,
    )
)


diagnostic_certified = (
    lineage_complete
)


report = {
    "stage":
        "Genesis Recall R4-R7",

    "purpose":
        (
            "Diagnostic Input Lineage "
            "+ 24-Case Provenance Reconciliation"
        ),

    "population": {
        "expected_cases":
            EXPECTED_SAMPLE,

        "actual_cases":
            len(
                case_records
            ),
    },

    "artifact_matches": {
        artifact:
            artifact_match_counter.get(
                artifact,
                0,
            )
        for artifact
        in ARTIFACT_ORDER
    },

    "first_divergence_census":
        dict(
            first_divergence_counter
        ),

    "field_mismatch_census":
        dict(
            mismatch_counter
        ),

    "lineage_result":
        lineage_result,

    "certification": {
        "exact_case_count":
            exact_case_count,

        "r4r2_trace_complete":
            r4r2_trace_complete,

        "r4r3_trace_complete":
            r4r3_trace_complete,

        "r4r4_trace_complete":
            r4r4_trace_complete,

        "r4r6_sample_trace_complete":
            r4r6_sample_trace_complete,

        "r4r6_population_trace_complete":
            r4r6_population_trace_complete,

        "r4r6r1_trace_complete":
            r4r6r1_trace_complete,

        "lineage_complete":
            lineage_complete,

        "diagnostic_certified":
            diagnostic_certified,
    },

    "cases":
        case_records,
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
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R7 RESULT")
print("=" * 78)


print()
print("POPULATION")

print(
    "  expected cases             :",
    EXPECTED_SAMPLE,
)

print(
    "  traced cases               :",
    len(
        case_records
    ),
)


print()
print("ARTIFACT LINEAGE MATCHES")

for artifact in ARTIFACT_ORDER:

    print(
        f"  {artifact:<24}:",
        artifact_match_counter.get(
            artifact,
            0,
        ),
        "/24",
    )


print()
print("FIRST DIVERGENCE CENSUS")

for artifact, count in (
    first_divergence_counter.most_common()
):

    print(
        f"  {artifact:<28}"
        f"{count:>3} "
        f"({100.0 * count / EXPECTED_SAMPLE:6.2f}%)"
    )


print()
print("FIELD MISMATCH CENSUS")

if mismatch_counter:

    for key, count in sorted(
        mismatch_counter.items(),
        key=lambda item:
            (
                -item[1],
                item[0],
            ),
    ):

        print(
            f"  {key:<42}"
            f"{count:>3}"
        )

else:

    print(
        "  NONE"
    )


print()
print("LINEAGE RESULT")

print(
    " ",
    lineage_result,
)


print()
print("CERTIFICATION")

print(
    "  exact case count           :",
    exact_case_count,
)

print(
    "  R4-R2 trace complete       :",
    r4r2_trace_complete,
)

print(
    "  R4-R3 trace complete       :",
    r4r3_trace_complete,
)

print(
    "  R4-R4 trace complete       :",
    r4r4_trace_complete,
)

print(
    "  R4-R6 sample trace complete:",
    r4r6_sample_trace_complete,
)

print(
    "  R4-R6 pop trace complete   :",
    r4r6_population_trace_complete,
)

print(
    "  R4-R6-R1 trace complete    :",
    r4r6r1_trace_complete,
)

print(
    "  lineage complete           :",
    lineage_complete,
)


print()
print(
    "R4-R7 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)


print()
print(
    "JSON report :",
    REPORT,
)

print(
    "detail TSV  :",
    DETAIL,
)

print(
    "mismatch TSV:",
    MISMATCH,
)

print(
    "trace       :",
    TRACE,
)

print("=" * 78)


raise SystemExit(
    0
    if diagnostic_certified
    else 1
)
