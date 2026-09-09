from __future__ import annotations

import csv
import json
import re
import time
import unicodedata

from collections import Counter
from pathlib import Path
from typing import Any


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

OUTDIR = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
)

R4_R5_REPORT = (
    OUTDIR
    / "r4_r5_lexical_zero_score_anatomy.json"
)

R4_R2_DETAIL = (
    OUTDIR
    / "r4_r2_qualification_drop_detail.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r6_token_divergence_root_cause.json"
)

SAMPLE_TSV = (
    OUTDIR
    / "r4_r6_token_divergence_sample.tsv"
)

POPULATION_TSV = (
    OUTDIR
    / "r4_r6_token_divergence_population.tsv"
)

CLASS_TSV = (
    OUTDIR
    / "r4_r6_divergence_class_census.tsv"
)


import core.retrieval.qualification.lexical as lex


# ============================================================
# EXACT PRODUCTION OBJECTS
# ============================================================

normalize_text = lex.normalize_text
canonicalize_token = lex.canonicalize_token
tokenize = lex.tokenize
analyze_lexical = lex.analyze_lexical

TOKEN_RE = lex.TOKEN_RE
STOP_WORDS = lex.STOP_WORDS


# ============================================================
# REFERENCE TOKENIZER
#
# This is NOT a proposed repair.
# It exists only to expose boundaries that production loses
# or treats differently.
# ============================================================

REFERENCE_RE = re.compile(
    r"[a-z0-9]+",
    re.IGNORECASE,
)


def reference_tokens(
    value: Any,
) -> tuple[str, ...]:

    return tuple(
        token.casefold()
        for token in REFERENCE_RE.findall(
            str(
                value
                or ""
            )
        )
        if token
    )


# ============================================================
# EXACT PRODUCTION PIPELINE TRACE
# ============================================================

def pipeline(
    value: Any,
) -> dict[str, Any]:

    raw = str(
        value
        or ""
    )

    normalized = normalize_text(
        raw
    )

    regex_raw = tuple(
        TOKEN_RE.findall(
            normalized
        )
    )


    regex_strings = []

    for item in regex_raw:

        if isinstance(
            item,
            tuple,
        ):

            # Defensive support if TOKEN_RE contains groups.
            joined = "".join(
                str(x)
                for x in item
                if x
            )

            regex_strings.append(
                joined
            )

        else:

            regex_strings.append(
                str(item)
            )


    canonical_steps = []

    retained = []

    stopword_removed = []

    empty_removed = []


    for raw_token in regex_strings:

        canonical = canonicalize_token(
            raw_token
        )

        is_empty = not bool(
            canonical
        )

        is_stopword = (
            bool(
                canonical
            )
            and
            canonical in STOP_WORDS
        )


        canonical_steps.append(
            {
                "regex_token":
                    raw_token,

                "canonical":
                    canonical,

                "empty":
                    is_empty,

                "stopword":
                    is_stopword,
            }
        )


        if is_empty:

            empty_removed.append(
                raw_token
            )

            continue


        if is_stopword:

            stopword_removed.append(
                canonical
            )

            continue


        retained.append(
            canonical
        )


    production = tuple(
        tokenize(
            raw
        )
    )


    if tuple(
        retained
    ) != production:

        pipeline_consistent = False

    else:

        pipeline_consistent = True


    reference = reference_tokens(
        raw
    )


    return {
        "raw":
            raw,

        "normalized":
            normalized,

        "regex_tokens":
            regex_strings,

        "canonical_steps":
            canonical_steps,

        "stopword_removed":
            stopword_removed,

        "empty_removed":
            empty_removed,

        "manual_retained":
            retained,

        "production_tokens":
            list(
                production
            ),

        "reference_tokens":
            list(
                reference
            ),

        "pipeline_consistent":
            pipeline_consistent,
    }


# ============================================================
# TOKEN COMPARISON
# ============================================================

def compare(
    query: str,
    candidate: str,
) -> dict[str, Any]:

    q = pipeline(
        query
    )

    c = pipeline(
        candidate
    )


    prod_q = tuple(
        q[
            "production_tokens"
        ]
    )

    prod_c = tuple(
        c[
            "production_tokens"
        ]
    )

    ref_q = tuple(
        q[
            "reference_tokens"
        ]
    )

    ref_c = tuple(
        c[
            "reference_tokens"
        ]
    )


    unique_prod_q = tuple(
        dict.fromkeys(
            prod_q
        )
    )

    unique_ref_q = tuple(
        dict.fromkeys(
            ref_q
        )
    )


    prod_candidate_set = set(
        prod_c
    )

    ref_candidate_set = set(
        ref_c
    )


    prod_matched = tuple(
        token
        for token in unique_prod_q
        if token in prod_candidate_set
    )

    ref_matched = tuple(
        token
        for token in unique_ref_q
        if token in ref_candidate_set
    )


    result = analyze_lexical(
        query,
        candidate,
    )


    production_score = float(
        result.score
    )


    # ========================================================
    # Divergence primitives
    # ========================================================

    query_reference_only = sorted(
        set(
            ref_q
        )
        -
        set(
            prod_q
        )
    )

    candidate_reference_only = sorted(
        set(
            ref_c
        )
        -
        set(
            prod_c
        )
    )

    query_production_only = sorted(
        set(
            prod_q
        )
        -
        set(
            ref_q
        )
    )

    candidate_production_only = sorted(
        set(
            prod_c
        )
        -
        set(
            ref_c
        )
    )


    # ========================================================
    # Root-cause classification
    # ========================================================

    classes = []


    # Stop-word removal can explain a generic/reference match
    # disappearing from the production token universe.
    removed_q = set(
        q[
            "stopword_removed"
        ]
    )

    removed_c = set(
        c[
            "stopword_removed"
        ]
    )

    if (
        set(
            ref_matched
        )
        &
        (
            removed_q
            |
            removed_c
        )
    ):

        classes.append(
            "STOP_WORD_FILTER_DIVERGENCE"
        )


    # Detect separator/boundary behavior by comparing reference
    # pieces with production tokens.
    ref_common = set(
        ref_matched
    )


    boundary_suspect = False

    for token in (
        list(
            prod_q
        )
        +
        list(
            prod_c
        )
    ):

        pieces = set(
            reference_tokens(
                token
            )
        )

        if (
            len(
                pieces
            )
            > 1
            and
            pieces
            &
            ref_common
        ):

            boundary_suspect = True
            break


    if boundary_suspect:

        classes.append(
            "TOKEN_BOUNDARY_OR_SEPARATOR_DIVERGENCE"
        )


    # Unicode/case normalization changed visible identity.
    raw_q_cf = str(
        query
    ).casefold()

    raw_c_cf = str(
        candidate
    ).casefold()

    norm_q_cf = str(
        q[
            "normalized"
        ]
    ).casefold()

    norm_c_cf = str(
        c[
            "normalized"
        ]
    ).casefold()


    if (
        raw_q_cf
        != norm_q_cf
        or
        raw_c_cf
        != norm_c_cf
    ):

        # Only classify if reference sees overlap but production
        # does not.
        if (
            ref_matched
            and
            not prod_matched
        ):

            classes.append(
                "NORMALIZE_TEXT_DIVERGENCE"
            )


    # Canonicalization changes regex tokens.
    canonical_changed = any(
        step[
            "regex_token"
        ]
        !=
        step[
            "canonical"
        ]
        for step in (
            q[
                "canonical_steps"
            ]
            +
            c[
                "canonical_steps"
            ]
        )
        if step[
            "canonical"
        ]
    )


    if (
        canonical_changed
        and
        ref_matched
        and
        not prod_matched
    ):

        classes.append(
            "CANONICALIZATION_DIVERGENCE"
        )


    # Filename / extension contamination.
    extension_pattern = re.compile(
        r"\.(?:pdf|epub|mobi|azw3|txt|html?|docx?|rtf|md|odt)$",
        re.IGNORECASE,
    )


    if (
        extension_pattern.search(
            str(
                candidate
            ).strip()
        )
        and
        ref_matched
        and
        not prod_matched
    ):

        classes.append(
            "FILENAME_EXTENSION_BOUNDARY_DIVERGENCE"
        )


    # Generic/reference sees common terms, but exact production
    # token equality sees none.
    if (
        ref_matched
        and
        not prod_matched
    ):

        classes.append(
            "REFERENCE_OVERLAP_BUT_NO_PRODUCTION_EXACT_MATCH"
        )


    if (
        not q[
            "pipeline_consistent"
        ]
        or
        not c[
            "pipeline_consistent"
        ]
    ):

        classes.append(
            "PIPELINE_RECONSTRUCTION_MISMATCH"
        )


    if (
        production_score
        == 0.0
        and
        prod_matched
    ):

        classes.append(
            "SCORING_ZERO_DESPITE_PRODUCTION_MATCH"
        )


    if not classes:

        if (
            production_score
            == 0.0
            and
            ref_matched
        ):

            classes.append(
                "UNCLASSIFIED_TOKEN_DIVERGENCE"
            )

        elif production_score == 0.0:

            classes.append(
                "NO_REFERENCE_OR_PRODUCTION_MATCH"
            )

        else:

            classes.append(
                "NO_FAILURE"
            )


    return {
        "query_pipeline":
            q,

        "candidate_pipeline":
            c,

        "production_matched":
            list(
                prod_matched
            ),

        "reference_matched":
            list(
                ref_matched
            ),

        "query_reference_only":
            query_reference_only,

        "candidate_reference_only":
            candidate_reference_only,

        "query_production_only":
            query_production_only,

        "candidate_production_only":
            candidate_production_only,

        "production_score":
            production_score,

        "production_analysis": {
            "query_tokens":
                list(
                    result.query_tokens
                ),

            "candidate_tokens":
                list(
                    result.candidate_tokens
                ),

            "matched_tokens":
                list(
                    result.matched_tokens
                ),

            "unique_coverage":
                float(
                    result.unique_coverage
                ),

            "weighted_coverage":
                float(
                    result.weighted_coverage
                ),
        },

        "classes":
            classes,
    }


# ============================================================
# INPUT HELPERS
# ============================================================

def first_present(
    row: dict[str, Any],
    names: tuple[str, ...],
) -> str:

    for name in names:

        value = row.get(
            name
        )

        if value is None:
            continue

        text = str(
            value
        )

        if text:
            return text

    return ""


def subject_candidate_text(
    row: dict[str, Any],
) -> tuple[str, str]:

    subject = first_present(
        row,
        (
            "candidate_subject",
            "subject",
            "raw_subject",
        ),
    )

    title = first_present(
        row,
        (
            "candidate_title",
            "title",
            "raw_title",
        ),
    )

    combined = " ".join(
        x
        for x in (
            subject,
            title,
        )
        if x
    )

    return (
        subject,
        title,
        combined,
    )


# ============================================================
# LOAD R4-R5 SAMPLE
# ============================================================

r4_r5 = json.loads(
    R4_R5_REPORT.read_text(
        encoding="utf-8"
    )
)

sample_cases = []

seen_sample = set()

for row in r4_r5[
    "records"
]:

    if row[
        "category"
    ] != "failure":
        continue

    if row[
        "form"
    ] != "SUBJECT_PLUS_TITLE":
        continue

    key = row[
        "name"
    ]

    if key in seen_sample:
        continue

    seen_sample.add(
        key
    )

    sample_cases.append(
        {
            "name":
                row[
                    "name"
                ],

            "query":
                row[
                    "query"
                ],

            "subject":
                row[
                    "subject"
                ],

            "title":
                row[
                    "title"
                ],

            "candidate_text":
                row[
                    "candidate_text"
                ],
        }
    )


if len(
    sample_cases
) != 24:

    raise RuntimeError(
        f"expected 24 R4-R5 cases, "
        f"found {len(sample_cases)}"
    )


# ============================================================
# LOAD FULL R4-R2 SUBJECT POPULATION
# ============================================================

with R4_R2_DETAIL.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    r4_r2_rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


subject_rows = [
    row
    for row in r4_r2_rows
    if str(
        row.get(
            "failure_class",
            ""
        )
    ).strip().upper()
    == "SUBJECT"
]


if len(
    subject_rows
) != 221:

    raise RuntimeError(
        "expected exact R4-R2 SUBJECT population "
        f"of 221, found {len(subject_rows)}"
    )


# ============================================================
# TRACE SAMPLE
# ============================================================

started = time.time()

sample_records = []


print("=" * 78)
print(" GENESIS RECALL R4-R6")
print(" PRODUCTION TOKEN DIVERGENCE ROOT-CAUSE TRACE")
print("=" * 78)


print()
print("=== A. DETERMINISTIC 24-CASE SAMPLE ===")


for index, case in enumerate(
    sample_cases,
    start=1,
):

    trace = compare(
        case[
            "query"
        ],
        case[
            "candidate_text"
        ],
    )

    record = {
        **case,
        **trace,
    }

    sample_records.append(
        record
    )


    print()
    print(
        f"[{index:02d}/24]",
        case[
            "name"
        ],
    )

    print(
        "  query raw:",
        case[
            "query"
        ],
    )

    print(
        "  candidate raw:",
        case[
            "candidate_text"
        ],
    )

    print(
        "  query normalized:",
        trace[
            "query_pipeline"
        ][
            "normalized"
        ],
    )

    print(
        "  candidate normalized:",
        trace[
            "candidate_pipeline"
        ][
            "normalized"
        ],
    )

    print(
        "  query regex tokens:",
        trace[
            "query_pipeline"
        ][
            "regex_tokens"
        ],
    )

    print(
        "  candidate regex tokens:",
        trace[
            "candidate_pipeline"
        ][
            "regex_tokens"
        ],
    )

    print(
        "  query production tokens:",
        trace[
            "query_pipeline"
        ][
            "production_tokens"
        ],
    )

    print(
        "  candidate production tokens:",
        trace[
            "candidate_pipeline"
        ][
            "production_tokens"
        ],
    )

    print(
        "  reference matched:",
        trace[
            "reference_matched"
        ],
    )

    print(
        "  production matched:",
        trace[
            "production_matched"
        ],
    )

    print(
        "  lexical score:",
        trace[
            "production_score"
        ],
    )

    print(
        "  classes:",
        trace[
            "classes"
        ],
    )


# ============================================================
# TRACE FULL 221 SUBJECT POPULATION
# ============================================================

population_records = []


print()
print("=== B. FULL 221 SUBJECT-FAILURE POPULATION ===")


for index, row in enumerate(
    subject_rows,
    start=1,
):

    query = first_present(
        row,
        (
            "query",
            "qualification_query",
        ),
    )

    subject, title, combined = (
        subject_candidate_text(
            row
        )
    )


    if not query:

        raise RuntimeError(
            f"row {index}: query unavailable"
        )

    if not combined:

        raise RuntimeError(
            f"row {index}: subject/title unavailable"
        )


    trace = compare(
        query,
        combined,
    )


    record = {
        "row_index":
            index,

        "document_id":
            first_present(
                row,
                (
                    "document_id",
                    "runtime_document_id",
                    "target_document_id",
                    "source_id",
                ),
            ),

        "query":
            query,

        "subject":
            subject,

        "title":
            title,

        "candidate_text":
            combined,

        **trace,
    }


    population_records.append(
        record
    )


# ============================================================
# CLASS CENSUS
# ============================================================

class_counter = Counter()

primary_counter = Counter()


for record in population_records:

    classes = record[
        "classes"
    ]

    for item in classes:
        class_counter[
            item
        ] += 1

    if classes:
        primary_counter[
            classes[0]
        ] += 1


# ============================================================
# EXACT FAILURE COUNTS
# ============================================================

production_zero = sum(
    1
    for row in population_records
    if row[
        "production_score"
    ]
    == 0.0
)


reference_overlap = sum(
    1
    for row in population_records
    if row[
        "reference_matched"
    ]
)


production_match = sum(
    1
    for row in population_records
    if row[
        "production_matched"
    ]
)


reference_overlap_prod_zero = sum(
    1
    for row in population_records
    if (
        row[
            "reference_matched"
        ]
        and
        row[
            "production_score"
        ]
        == 0.0
    )
)


reference_overlap_no_prod_match = sum(
    1
    for row in population_records
    if (
        row[
            "reference_matched"
        ]
        and
        not row[
            "production_matched"
        ]
    )
)


pipeline_mismatch = sum(
    1
    for row in population_records
    if (
        not row[
            "query_pipeline"
        ][
            "pipeline_consistent"
        ]
        or
        not row[
            "candidate_pipeline"
        ][
            "pipeline_consistent"
        ]
    )
)


# ============================================================
# DOMINANT ROOT CAUSE
# ============================================================

if class_counter:

    dominant_class, dominant_count = (
        class_counter.most_common(
            1
        )[0]
    )

else:

    dominant_class = "NONE"
    dominant_count = 0


dominant_pct = (
    100.0
    * dominant_count
    / len(
        population_records
    )
    if population_records
    else 0.0
)


# ============================================================
# HOMOGENEITY / REPAIRABILITY SIGNAL
#
# Certification does NOT mean a repair is safe.
# It means the token divergence has been deterministically
# measured across the exact 221-row population.
# ============================================================

single_dominant_rule = (
    dominant_count
    == len(
        population_records
    )
)


near_universal_rule = (
    dominant_pct
    >= 95.0
)


if single_dominant_rule:

    root_cause_scope = (
        "UNIVERSAL_SINGLE_CLASS"
    )

elif near_universal_rule:

    root_cause_scope = (
        "NEAR_UNIVERSAL_DOMINANT_CLASS"
    )

else:

    root_cause_scope = (
        "MULTIPLE_DIVERGENCE_CLASSES"
    )


# ============================================================
# WRITE SAMPLE TSV
# ============================================================

sample_fields = [
    "name",
    "query",
    "candidate_text",
    "production_score",
    "reference_matched",
    "production_matched",
    "query_reference_only",
    "candidate_reference_only",
    "classes",
]


with SAMPLE_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=sample_fields,
        delimiter="\t",
    )

    writer.writeheader()

    for row in sample_records:

        writer.writerow(
            {
                "name":
                    row[
                        "name"
                    ],

                "query":
                    row[
                        "query"
                    ],

                "candidate_text":
                    row[
                        "candidate_text"
                    ],

                "production_score":
                    row[
                        "production_score"
                    ],

                "reference_matched":
                    ",".join(
                        row[
                            "reference_matched"
                        ]
                    ),

                "production_matched":
                    ",".join(
                        row[
                            "production_matched"
                        ]
                    ),

                "query_reference_only":
                    ",".join(
                        row[
                            "query_reference_only"
                        ]
                    ),

                "candidate_reference_only":
                    ",".join(
                        row[
                            "candidate_reference_only"
                        ]
                    ),

                "classes":
                    ",".join(
                        row[
                            "classes"
                        ]
                    ),
            }
        )


# ============================================================
# WRITE POPULATION TSV
# ============================================================

population_fields = [
    "row_index",
    "document_id",
    "query",
    "subject",
    "title",
    "production_score",
    "reference_matched",
    "production_matched",
    "query_production_tokens",
    "candidate_production_tokens",
    "query_reference_tokens",
    "candidate_reference_tokens",
    "query_reference_only",
    "candidate_reference_only",
    "query_production_only",
    "candidate_production_only",
    "classes",
]


with POPULATION_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=population_fields,
        delimiter="\t",
    )

    writer.writeheader()

    for row in population_records:

        writer.writerow(
            {
                "row_index":
                    row[
                        "row_index"
                    ],

                "document_id":
                    row[
                        "document_id"
                    ],

                "query":
                    row[
                        "query"
                    ],

                "subject":
                    row[
                        "subject"
                    ],

                "title":
                    row[
                        "title"
                    ],

                "production_score":
                    row[
                        "production_score"
                    ],

                "reference_matched":
                    ",".join(
                        row[
                            "reference_matched"
                        ]
                    ),

                "production_matched":
                    ",".join(
                        row[
                            "production_matched"
                        ]
                    ),

                "query_production_tokens":
                    ",".join(
                        row[
                            "query_pipeline"
                        ][
                            "production_tokens"
                        ]
                    ),

                "candidate_production_tokens":
                    ",".join(
                        row[
                            "candidate_pipeline"
                        ][
                            "production_tokens"
                        ]
                    ),

                "query_reference_tokens":
                    ",".join(
                        row[
                            "query_pipeline"
                        ][
                            "reference_tokens"
                        ]
                    ),

                "candidate_reference_tokens":
                    ",".join(
                        row[
                            "candidate_pipeline"
                        ][
                            "reference_tokens"
                        ]
                    ),

                "query_reference_only":
                    ",".join(
                        row[
                            "query_reference_only"
                        ]
                    ),

                "candidate_reference_only":
                    ",".join(
                        row[
                            "candidate_reference_only"
                        ]
                    ),

                "query_production_only":
                    ",".join(
                        row[
                            "query_production_only"
                        ]
                    ),

                "candidate_production_only":
                    ",".join(
                        row[
                            "candidate_production_only"
                        ]
                    ),

                "classes":
                    ",".join(
                        row[
                            "classes"
                        ]
                    ),
            }
        )


# ============================================================
# WRITE CLASS CENSUS
# ============================================================

with CLASS_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.writer(
        f,
        delimiter="\t",
    )

    writer.writerow(
        (
            "divergence_class",
            "count",
            "percent_of_221",
        )
    )

    for name, count in (
        class_counter.most_common()
    ):

        writer.writerow(
            (
                name,
                count,
                (
                    100.0
                    * count
                    / 221
                ),
            )
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
        "R4-R6",

    "purpose":
        (
            "Production Token Divergence "
            "& Canonicalization Root-Cause Certification"
        ),

    "population": {
        "r4_r5_sample":
            len(
                sample_records
            ),

        "r4_r2_subject_failures":
            len(
                population_records
            ),
    },

    "pipeline": {
        "token_re":
            repr(
                TOKEN_RE
            ),

        "stop_word_count":
            len(
                STOP_WORDS
            ),
    },

    "population_results": {
        "production_score_zero":
            production_zero,

        "reference_overlap":
            reference_overlap,

        "production_exact_match":
            production_match,

        "reference_overlap_and_production_zero":
            reference_overlap_prod_zero,

        "reference_overlap_but_no_production_match":
            reference_overlap_no_prod_match,

        "pipeline_reconstruction_mismatch":
            pipeline_mismatch,
    },

    "divergence_classes":
        dict(
            class_counter
        ),

    "primary_classes":
        dict(
            primary_counter
        ),

    "dominant_root_cause": {
        "class":
            dominant_class,

        "count":
            dominant_count,

        "percent":
            dominant_pct,

        "scope":
            root_cause_scope,
    },

    "sample_records":
        sample_records,

    "population_records":
        population_records,

    "elapsed_seconds":
        round(
            elapsed,
            3,
        ),
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
# RESULT
# ============================================================

print()
print("=" * 78)
print(" GENESIS RECALL R4-R6 RESULT")
print("=" * 78)


print()
print("POPULATION")

print(
    "  deterministic sample      :",
    len(
        sample_records
    ),
)

print(
    "  full SUBJECT failures     :",
    len(
        population_records
    ),
)


print()
print("PRODUCTION TOKEN BEHAVIOR")

print(
    "  production lexical = 0    :",
    production_zero,
    "/221",
)

print(
    "  reference overlap > 0     :",
    reference_overlap,
    "/221",
)

print(
    "  production exact match >0 :",
    production_match,
    "/221",
)

print(
    "  ref overlap + prod zero   :",
    reference_overlap_prod_zero,
    "/221",
)

print(
    "  ref overlap/no prod match :",
    reference_overlap_no_prod_match,
    "/221",
)

print(
    "  pipeline reconstruction"
    " mismatch                  :",
    pipeline_mismatch,
)


print()
print("DIVERGENCE CLASS CENSUS")

for name, count in (
    class_counter.most_common()
):

    pct = (
        100.0
        * count
        / len(
            population_records
        )
    )

    print(
        f"  {name:<48}"
        f"{count:>4} "
        f"({pct:6.2f}%)"
    )


print()
print("DOMINANT ROOT CAUSE")

print(
    "  class   :",
    dominant_class,
)

print(
    "  count   :",
    dominant_count,
)

print(
    "  percent :",
    round(
        dominant_pct,
        2,
    ),
)

print(
    "  scope   :",
    root_cause_scope,
)


print()
print("PIPELINE")

print(
    "  TOKEN_RE       :",
    repr(
        TOKEN_RE
    ),
)

print(
    "  STOP_WORDS     :",
    len(
        STOP_WORDS
    ),
)


complete = (
    len(
        sample_records
    )
    == 24
    and
    len(
        population_records
    )
    == 221
    and
    pipeline_mismatch
    == 0
)


print()
print("CERTIFICATION")

print(
    "  exact R4-R5 sample       :",
    len(
        sample_records
    )
    == 24,
)

print(
    "  exact SUBJECT population :",
    len(
        population_records
    )
    == 221,
)

print(
    "  exact production pipeline:",
    pipeline_mismatch
    == 0,
)

print(
    "  root-cause census complete:",
    bool(
        class_counter
    ),
)

print()
print(
    "R4-R6 DIAGNOSTIC CERTIFIED:",
    complete,
)


print()
print(
    "JSON report :",
    REPORT,
)

print(
    "sample TSV  :",
    SAMPLE_TSV,
)

print(
    "population  :",
    POPULATION_TSV,
)

print(
    "class census:",
    CLASS_TSV,
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
