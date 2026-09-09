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

OUTDIR = (
    PROJECT
    / "artifacts"
    / "genesis_recall"
)

R4R2 = (
    OUTDIR
    / "r4_r2_qualification_drop_detail.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r9_subject_lexical_differential.json"
)

DETAIL = (
    OUTDIR
    / "r4_r9_subject_lexical_differential.tsv"
)

CLASS_TSV = (
    OUTDIR
    / "r4_r9_differential_class_census.tsv"
)

TOKEN_TSV = (
    OUTDIR
    / "r4_r9_token_stream_detail.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r9_subject_lexical_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r9_lexical_subject_source_map.txt"
)


sys.path.insert(
    0,
    str(PROJECT),
)


from core.knowledge_catalog.search import (
    search_catalog,
)

from core.knowledge_catalog.qualified_search import (
    candidate_from_row,
)

from core.retrieval.qualification.contracts import (
    EvidenceCandidate,
)

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)

import core.retrieval.qualification.lexical as lexical_module

from core.retrieval.qualification.lexical import (
    analyze_lexical,
    canonicalize_token,
    normalize_text,
    tokenize,
)

from core.retrieval.qualification.subject import (
    analyze_subject,
)


TOKEN_RE = lexical_module.TOKEN_RE
STOP_WORDS = lexical_module.STOP_WORDS


EXPECTED_POPULATION = 221


# ============================================================
# BASIC HELPERS
# ============================================================

def sval(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(
        value
    )


def first_present(
    row: Mapping[str, Any],
    names: tuple[str, ...],
) -> str:

    for name in names:

        value = row.get(
            name
        )

        if value not in (
            None,
            "",
        ):

            return str(
                value
            )

    return ""


def raw_map(
    raw: Any,
) -> dict[str, Any]:

    if isinstance(
        raw,
        Mapping,
    ):

        return dict(
            raw
        )

    if hasattr(
        raw,
        "keys",
    ):

        try:

            return {
                key:
                    raw[
                        key
                    ]
                for key
                in raw.keys()
            }

        except Exception:
            pass

    if hasattr(
        raw,
        "_asdict",
    ):

        try:

            return dict(
                raw._asdict()
            )

        except Exception:
            pass

    try:

        return dict(
            vars(
                raw
            )
        )

    except Exception:

        return {}


def raw_identity_values(
    row: Mapping[str, Any],
) -> set[str]:

    result = set()

    for name in (
        "id",
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "source_id",
        "doc_id",
    ):

        value = row.get(
            name
        )

        if value not in (
            None,
            "",
        ):

            result.add(
                str(
                    value
                ).strip()
            )

    return result


def load_r4r2() -> list[dict[str, str]]:

    with R4R2.open(
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


def reference_tokens(
    text: str,
) -> tuple[str, ...]:

    return tuple(
        token.casefold()
        for token in re.findall(
            r"[A-Za-z0-9]+",
            sval(
                text
            ),
        )
        if token
    )


def unique_intersection(
    query_tokens: tuple[str, ...],
    candidate_tokens: tuple[str, ...],
) -> tuple[str, ...]:

    candidate_set = set(
        candidate_tokens
    )

    return tuple(
        token
        for token
        in dict.fromkeys(
            query_tokens
        )
        if token
        in candidate_set
    )


def analysis_dict(
    analysis: Any,
) -> dict[str, Any]:

    return {
        "score":
            float(
                analysis.score
            ),

        "query_tokens":
            list(
                analysis.query_tokens
            ),

        "candidate_tokens":
            list(
                analysis.candidate_tokens
            ),

        "matched_tokens":
            list(
                analysis.matched_tokens
            ),

        "unique_coverage":
            float(
                analysis.unique_coverage
            ),

        "weighted_coverage":
            float(
                analysis.weighted_coverage
            ),
    }


def token_pipeline(
    value: str,
) -> dict[str, Any]:

    raw = sval(
        value
    )

    normalized = normalize_text(
        raw
    )

    regex_tokens = list(
        TOKEN_RE.findall(
            normalized
        )
    )

    canonical = []

    stop_removed = []

    retained = []

    for item in regex_tokens:

        token = canonicalize_token(
            item
        )

        canonical.append(
            {
                "raw":
                    item,

                "canonical":
                    token,
            }
        )

        if not token:
            continue

        if token in STOP_WORDS:

            stop_removed.append(
                token
            )

            continue

        retained.append(
            token
        )

    production = list(
        tokenize(
            raw
        )
    )

    return {
        "raw":
            raw,

        "normalized":
            normalized,

        "regex_tokens":
            regex_tokens,

        "canonical_steps":
            canonical,

        "stopword_removed":
            stop_removed,

        "production_tokens":
            production,

        "manual_pipeline_matches":
            production
            == retained,

        "reference_tokens":
            list(
                reference_tokens(
                    raw
                )
            ),
    }


# ============================================================
# LOAD EXACT R4-R2 SUBJECT FAILURE POPULATION
# ============================================================

r4_rows = load_r4r2()

subject_failures = [
    row
    for row in r4_rows
    if (
        row.get(
            "failure_class",
            "",
        ).strip().upper()
        == "SUBJECT"
        or
        "SUBJECT"
        in row.get(
            "decision",
            "",
        ).upper()
        or
        "SUBJECT"
        in row.get(
            "qualification_decision",
            "",
        ).upper()
    )
]


if len(
    subject_failures
) != EXPECTED_POPULATION:

    raise RuntimeError(
        "Expected exactly 221 R4-R2 SUBJECT failures, "
        f"found {len(subject_failures)}"
    )


headers = tuple(
    r4_rows[
        0
    ].keys()
)


id_columns = tuple(
    name
    for name in headers
    if any(
        marker in name.casefold()
        for marker in (
            "document_id",
            "runtime_id",
            "source_id",
            "target_id",
            "doc_id",
        )
    )
)


def extract_query(
    row: Mapping[str, str],
) -> str:

    value = first_present(
        row,
        (
            "query",
            "search_query",
            "qualification_query",
            "input_query",
        ),
    )

    return value


def extract_target_ids(
    row: Mapping[str, str],
) -> set[str]:

    result = set()

    for name in (
        "document_id",
        "runtime_document_id",
        "runtime_id",
        "target_id",
        "doc_id",
        "source_id",
    ):

        value = row.get(
            name
        )

        if value not in (
            None,
            "",
        ):

            result.add(
                str(
                    value
                ).strip()
            )

    for name in id_columns:

        value = row.get(
            name
        )

        if value not in (
            None,
            "",
        ):

            result.add(
                str(
                    value
                ).strip()
            )

    return {
        item
        for item in result
        if item
    }


# ============================================================
# TRACE EXACT PRODUCTION CANDIDATES
# ============================================================

engine = QualificationEngine()

started = time.time()

records = []

token_rows = []

trace_lines = []

class_counter = Counter()

component_counter = Counter()

pipeline_mismatch = 0

target_missing = 0

multiple_raw_match = 0

subject_analysis_parity_failure = 0

engine_main_parity_failure = 0


for index, r4 in enumerate(
    subject_failures,
    start=1,
):

    query = extract_query(
        r4
    )

    target_ids = extract_target_ids(
        r4
    )

    if not query:

        raise RuntimeError(
            f"case {index}: query unavailable"
        )

    if not target_ids:

        raise RuntimeError(
            f"case {index}: target identity unavailable"
        )


    raw_rows = list(
        search_catalog(
            query,
            limit=100,
        )
    )


    matches = []

    for ordinal, raw in enumerate(
        raw_rows,
        start=1,
    ):

        mapped = raw_map(
            raw
        )

        identities = raw_identity_values(
            mapped
        )

        if target_ids.intersection(
            identities
        ):

            matches.append(
                (
                    ordinal,
                    raw,
                    mapped,
                )
            )


    if not matches:

        target_missing += 1

        records.append(
            {
                "case":
                    index,

                "query":
                    query,

                "target_ids":
                    "|".join(
                        sorted(
                            target_ids
                        )
                    ),

                "status":
                    "TARGET_RAW_NOT_FOUND",
            }
        )

        continue


    if len(
        matches
    ) > 1:

        multiple_raw_match += 1


    ordinal, raw, mapped = matches[
        0
    ]


    candidate = candidate_from_row(
        raw,
        ordinal=ordinal,
    )


    if not isinstance(
        candidate,
        EvidenceCandidate,
    ):

        raise RuntimeError(
            f"case {index}: candidate contract failure"
        )


    # ========================================================
    # EXACT PRODUCTION TEXT INPUTS
    # ========================================================

    subject_text = " ".join(
        x
        for x in (
            candidate.subject,
            candidate.title,
        )
        if x
    )


    main_text = " ".join(
        x
        for x in (
            candidate.title,
            candidate.subject,
            candidate.excerpt,
            candidate.source_path,
        )
        if x
    )


    # ========================================================
    # ACTUAL PRODUCTION ANALYSES
    # ========================================================

    main_analysis = analyze_lexical(
        query,
        main_text,
    )

    subject_lexical = analyze_lexical(
        query,
        subject_text,
    )

    subject_analysis = analyze_subject(
        query,
        candidate.subject,
        candidate.title,
    )


    engine_result = engine.evaluate(
        query,
        (
            candidate,
        ),
    )


    evidence_items = (
        *engine_result.accepted,
        *engine_result.rejected,
    )


    if len(
        evidence_items
    ) != 1:

        raise RuntimeError(
            f"case {index}: unexpected engine evidence cardinality "
            f"{len(evidence_items)}"
        )


    evidence = evidence_items[
        0
    ]

    engine_main_score = float(
        evidence.score.lexical
    )

    engine_subject_score = float(
        evidence.score.subject
    )


    if not math.isclose(
        engine_main_score,
        float(
            main_analysis.score
        ),
        abs_tol=1e-12,
    ):

        engine_main_parity_failure += 1


    if not math.isclose(
        float(
            subject_analysis.score
        ),
        float(
            subject_lexical.score
        ),
        abs_tol=1e-12,
    ):

        subject_analysis_parity_failure += 1


    # ========================================================
    # COMPONENT-LEVEL LEXICAL CONTRIBUTIONS
    # ========================================================

    title_analysis = analyze_lexical(
        query,
        candidate.title,
    )

    candidate_subject_analysis = analyze_lexical(
        query,
        candidate.subject,
    )

    excerpt_analysis = analyze_lexical(
        query,
        candidate.excerpt,
    )

    source_path_analysis = analyze_lexical(
        query,
        candidate.source_path,
    )


    components = {
        "TITLE":
            title_analysis,

        "SUBJECT":
            candidate_subject_analysis,

        "EXCERPT":
            excerpt_analysis,

        "SOURCE_PATH":
            source_path_analysis,
    }


    positive_components = [
        name
        for name, analysis
        in components.items()
        if float(
            analysis.score
        )
        > 0.0
    ]


    for name in positive_components:

        component_counter[
            name
        ] += 1


    # ========================================================
    # TOKEN PIPELINES
    # ========================================================

    query_pipeline = token_pipeline(
        query
    )

    subject_pipeline = token_pipeline(
        subject_text
    )

    main_pipeline = token_pipeline(
        main_text
    )

    title_pipeline = token_pipeline(
        candidate.title
    )

    candidate_subject_pipeline = token_pipeline(
        candidate.subject
    )

    excerpt_pipeline = token_pipeline(
        candidate.excerpt
    )

    source_path_pipeline = token_pipeline(
        candidate.source_path
    )


    for pipe in (
        query_pipeline,
        subject_pipeline,
        main_pipeline,
        title_pipeline,
        candidate_subject_pipeline,
        excerpt_pipeline,
        source_path_pipeline,
    ):

        if not pipe[
            "manual_pipeline_matches"
        ]:

            pipeline_mismatch += 1


    # ========================================================
    # REFERENCE BOUNDARY ANALYSIS
    # ========================================================

    reference_query = reference_tokens(
        query
    )

    reference_subject = reference_tokens(
        subject_text
    )

    reference_main = reference_tokens(
        main_text
    )


    reference_subject_match = unique_intersection(
        reference_query,
        reference_subject,
    )

    production_subject_match = tuple(
        subject_lexical.matched_tokens
    )

    reference_main_match = unique_intersection(
        reference_query,
        reference_main,
    )

    production_main_match = tuple(
        main_analysis.matched_tokens
    )


    # ========================================================
    # ROOT-CAUSE CLASSIFICATION
    # ========================================================

    if (
        float(
            subject_lexical.score
        )
        == 0.0
        and
        reference_subject_match
        and
        not production_subject_match
    ):

        primary_class = (
            "SUBJECT_TOKEN_BOUNDARY_DIVERGENCE"
        )


    elif (
        float(
            subject_lexical.score
        )
        == 0.0
        and
        not reference_subject_match
        and
        not production_subject_match
    ):

        primary_class = (
            "SUBJECT_TEXT_NO_TOKEN_OVERLAP"
        )


    elif (
        float(
            subject_lexical.score
        )
        == 0.0
        and
        production_subject_match
    ):

        primary_class = (
            "SUBJECT_SCORING_ZERO_DESPITE_EXACT_MATCH"
        )


    elif float(
        subject_lexical.score
    ) > 0.0:

        primary_class = (
            "SUBJECT_LEXICAL_POSITIVE"
        )


    else:

        primary_class = (
            "UNCLASSIFIED_SUBJECT_DIFFERENTIAL"
        )


    class_counter[
        primary_class
    ] += 1


    # ========================================================
    # MAIN-vs-SUBJECT DIFFERENTIAL SOURCE
    # ========================================================

    extra_main_matches = sorted(
        set(
            main_analysis.matched_tokens
        )
        -
        set(
            subject_lexical.matched_tokens
        )
    )


    if (
        float(
            main_analysis.score
        )
        > 0.0
        and
        float(
            subject_lexical.score
        )
        == 0.0
    ):

        if (
            float(
                excerpt_analysis.score
            )
            > 0.0
            and
            float(
                source_path_analysis.score
            )
            > 0.0
        ):

            differential_source = (
                "EXCERPT_AND_SOURCE_PATH"
            )


        elif float(
            excerpt_analysis.score
        ) > 0.0:

            differential_source = (
                "EXCERPT"
            )


        elif float(
            source_path_analysis.score
        ) > 0.0:

            differential_source = (
                "SOURCE_PATH"
            )


        elif float(
            title_analysis.score
        ) > 0.0:

            differential_source = (
                "TITLE"
            )


        elif float(
            candidate_subject_analysis.score
        ) > 0.0:

            differential_source = (
                "SUBJECT"
            )


        else:

            differential_source = (
                "COMBINED_MAIN_TEXT_ONLY"
            )


    elif math.isclose(
        float(
            main_analysis.score
        ),
        float(
            subject_lexical.score
        ),
        abs_tol=1e-12,
    ):

        differential_source = (
            "NO_DIFFERENTIAL"
        )


    else:

        differential_source = (
            "OTHER"
        )


    component_counter[
        "DIFFERENTIAL:"
        + differential_source
    ] += 1


    # ========================================================
    # RECORD
    # ========================================================

    record = {
        "case":
            index,

        "status":
            "OK",

        "document_id":
            first_present(
                r4,
                (
                    "document_id",
                ),
            ),

        "query":
            query,

        "raw_rank":
            ordinal,

        "candidate_source_id":
            candidate.source_id,

        "candidate_title":
            candidate.title,

        "candidate_subject":
            candidate.subject,

        "candidate_source_path":
            candidate.source_path,

        "candidate_excerpt":
            candidate.excerpt,

        "main_text":
            main_text,

        "subject_text":
            subject_text,

        "main_lexical_score":
            float(
                main_analysis.score
            ),

        "subject_lexical_score":
            float(
                subject_lexical.score
            ),

        "subject_analysis_score":
            float(
                subject_analysis.score
            ),

        "engine_main_lexical_score":
            engine_main_score,

        "engine_subject_score":
            engine_subject_score,

        "title_score":
            float(
                title_analysis.score
            ),

        "candidate_subject_score":
            float(
                candidate_subject_analysis.score
            ),

        "excerpt_score":
            float(
                excerpt_analysis.score
            ),

        "source_path_score":
            float(
                source_path_analysis.score
            ),

        "production_query_tokens":
            ",".join(
                main_analysis.query_tokens
            ),

        "production_subject_tokens":
            ",".join(
                subject_lexical.candidate_tokens
            ),

        "production_main_tokens":
            ",".join(
                main_analysis.candidate_tokens
            ),

        "production_subject_matches":
            ",".join(
                subject_lexical.matched_tokens
            ),

        "production_main_matches":
            ",".join(
                main_analysis.matched_tokens
            ),

        "reference_subject_matches":
            ",".join(
                reference_subject_match
            ),

        "reference_main_matches":
            ",".join(
                reference_main_match
            ),

        "extra_main_matches":
            ",".join(
                extra_main_matches
            ),

        "positive_components":
            ",".join(
                positive_components
            ),

        "differential_source":
            differential_source,

        "primary_class":
            primary_class,

        "decision":
            str(
                evidence.decision
            ),

        "explanation":
            evidence.explanation,
    }


    records.append(
        record
    )


    token_rows.append(
        {
            "case":
                index,

            "query":
                query,

            "query_raw":
                query_pipeline[
                    "raw"
                ],

            "query_normalized":
                query_pipeline[
                    "normalized"
                ],

            "query_regex_tokens":
                json.dumps(
                    query_pipeline[
                        "regex_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "query_production_tokens":
                json.dumps(
                    query_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "query_reference_tokens":
                json.dumps(
                    query_pipeline[
                        "reference_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "subject_raw":
                subject_pipeline[
                    "raw"
                ],

            "subject_normalized":
                subject_pipeline[
                    "normalized"
                ],

            "subject_regex_tokens":
                json.dumps(
                    subject_pipeline[
                        "regex_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "subject_production_tokens":
                json.dumps(
                    subject_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "subject_reference_tokens":
                json.dumps(
                    subject_pipeline[
                        "reference_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "subject_production_matches":
                json.dumps(
                    list(
                        production_subject_match
                    ),
                    ensure_ascii=False,
                ),

            "subject_reference_matches":
                json.dumps(
                    list(
                        reference_subject_match
                    ),
                    ensure_ascii=False,
                ),

            "main_production_tokens":
                json.dumps(
                    main_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "main_production_matches":
                json.dumps(
                    list(
                        production_main_match
                    ),
                    ensure_ascii=False,
                ),

            "main_reference_matches":
                json.dumps(
                    list(
                        reference_main_match
                    ),
                    ensure_ascii=False,
                ),

            "title_production_tokens":
                json.dumps(
                    title_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "candidate_subject_production_tokens":
                json.dumps(
                    candidate_subject_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "excerpt_production_tokens":
                json.dumps(
                    excerpt_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),

            "source_path_production_tokens":
                json.dumps(
                    source_path_pipeline[
                        "production_tokens"
                    ],
                    ensure_ascii=False,
                ),
        }
    )


    # First 16 cases in human-readable trace.
    if index <= 16:

        trace_lines.extend(
            [
                "=" * 78,
                f"CASE {index:03d}",
                "=" * 78,

                f"document_id  : {record['document_id']}",
                f"query        : {query}",
                f"title        : {candidate.title}",
                f"subject      : {candidate.subject}",
                f"source_path  : {candidate.source_path}",

                "",
                "QUERY TOKEN PIPELINE",
                f"  normalized : {query_pipeline['normalized']}",
                f"  regex      : {query_pipeline['regex_tokens']}",
                f"  production : {query_pipeline['production_tokens']}",
                f"  reference  : {query_pipeline['reference_tokens']}",

                "",
                "SUBJECT+TITLE TOKEN PIPELINE",
                f"  raw        : {subject_text}",
                f"  normalized : {subject_pipeline['normalized']}",
                f"  regex      : {subject_pipeline['regex_tokens']}",
                f"  production : {subject_pipeline['production_tokens']}",
                f"  reference  : {subject_pipeline['reference_tokens']}",

                "",
                "SUBJECT PATH",
                f"  production matched : {list(production_subject_match)}",
                f"  reference matched  : {list(reference_subject_match)}",
                f"  lexical score      : {subject_lexical.score}",
                f"  analyze_subject    : {subject_analysis.score}",
                f"  engine subject     : {engine_subject_score}",

                "",
                "MAIN LEXICAL PATH",
                f"  production matched : {list(production_main_match)}",
                f"  reference matched  : {list(reference_main_match)}",
                f"  lexical score      : {main_analysis.score}",
                f"  engine lexical     : {engine_main_score}",
                f"  extra main matches : {extra_main_matches}",

                "",
                "COMPONENT SCORES",
                f"  title       : {title_analysis.score}",
                f"  subject     : {candidate_subject_analysis.score}",
                f"  excerpt     : {excerpt_analysis.score}",
                f"  source_path : {source_path_analysis.score}",

                "",
                f"DIFFERENTIAL SOURCE : {differential_source}",
                f"PRIMARY CLASS       : {primary_class}",
                "",
            ]
        )


# ============================================================
# POPULATION COUNTS
# ============================================================

ok_records = [
    row
    for row in records
    if row.get(
        "status"
    )
    == "OK"
]


main_positive = sum(
    1
    for row in ok_records
    if float(
        row[
            "main_lexical_score"
        ]
    )
    > 0.0
)


subject_zero = sum(
    1
    for row in ok_records
    if float(
        row[
            "subject_lexical_score"
        ]
    )
    == 0.0
)


subject_analyzer_zero = sum(
    1
    for row in ok_records
    if float(
        row[
            "subject_analysis_score"
        ]
    )
    == 0.0
)


main_positive_subject_zero = sum(
    1
    for row in ok_records
    if (
        float(
            row[
                "main_lexical_score"
            ]
        )
        > 0.0
        and
        float(
            row[
                "subject_lexical_score"
            ]
        )
        == 0.0
    )
)


reference_subject_overlap = sum(
    1
    for row in ok_records
    if row[
        "reference_subject_matches"
    ]
)


production_subject_overlap = sum(
    1
    for row in ok_records
    if row[
        "production_subject_matches"
    ]
)


# ============================================================
# DOMINANT CLASS
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
        ok_records
    )
    if ok_records
    else 0.0
)


# ============================================================
# WRITE DETAIL
# ============================================================

detail_fields = sorted(
    {
        key
        for row in records
        for key in row.keys()
    }
)


with DETAIL.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=detail_fields,
        delimiter="\t",
        extrasaction="ignore",
    )

    writer.writeheader()

    writer.writerows(
        records
    )


# ============================================================
# WRITE TOKEN DETAIL
# ============================================================

token_fields = sorted(
    {
        key
        for row in token_rows
        for key in row.keys()
    }
)


with TOKEN_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.DictWriter(
        handle,
        fieldnames=token_fields,
        delimiter="\t",
        extrasaction="ignore",
    )

    writer.writeheader()

    writer.writerows(
        token_rows
    )


# ============================================================
# WRITE CLASS CENSUS
# ============================================================

with CLASS_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as handle:

    writer = csv.writer(
        handle,
        delimiter="\t",
    )

    writer.writerow(
        (
            "class",
            "count",
            "percent_of_221",
        )
    )

    for name, count in class_counter.most_common():

        writer.writerow(
            (
                name,
                count,
                (
                    100.0
                    * count
                    / EXPECTED_POPULATION
                ),
            )
        )


# ============================================================
# WRITE TRACE
# ============================================================

TRACE.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R9",
            " EXACT SUBJECT ANALYZER TOKEN STREAM TRACE",
            "=" * 78,
            "",
            *trace_lines,
        )
    ),
    encoding="utf-8",
)


# ============================================================
# SOURCE MAP
# ============================================================

source_parts = []


for name, obj in (
    (
        "analyze_subject",
        analyze_subject,
    ),
    (
        "analyze_lexical",
        analyze_lexical,
    ),
    (
        "normalize_text",
        normalize_text,
    ),
    (
        "canonicalize_token",
        canonicalize_token,
    ),
    (
        "tokenize",
        tokenize,
    ),
    (
        "QualificationEngine.evaluate_candidate",
        QualificationEngine.evaluate_candidate,
    ),
):

    source_parts.extend(
        (
            "=" * 78,
            name,
            "=" * 78,
        )
    )

    try:

        source_parts.append(
            inspect.getsource(
                obj
            )
        )

    except Exception as exc:

        source_parts.append(
            f"SOURCE ERROR: "
            f"{type(exc).__name__}: {exc}"
        )


source_parts.extend(
    (
        "=" * 78,
        "TOKEN_RE / STOP_WORDS",
        "=" * 78,
        f"TOKEN_RE={TOKEN_RE!r}",
        f"STOP_WORDS={sorted(STOP_WORDS)!r}",
    )
)


SOURCE_MAP.write_text(
    "\n".join(
        source_parts
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# CERTIFICATION
# ============================================================

elapsed = (
    time.time()
    - started
)


certification = {
    "exact_population":
        len(
            subject_failures
        )
        == EXPECTED_POPULATION,

    "all_targets_traced":
        len(
            ok_records
        )
        == EXPECTED_POPULATION
        and
        target_missing
        == 0,

    "engine_main_lexical_parity":
        engine_main_parity_failure
        == 0,

    "subject_wrapper_parity":
        subject_analysis_parity_failure
        == 0,

    "token_pipeline_exact":
        pipeline_mismatch
        == 0,

    "differential_census_complete":
        sum(
            class_counter.values()
        )
        == EXPECTED_POPULATION,
}


certified = all(
    certification.values()
)


report = {
    "phase":
        "Genesis Recall R4-R9",

    "purpose":
        (
            "Exact Subject Analyzer Token Stream & "
            "Production Lexical Differential Certification"
        ),

    "population": {
        "subject_failures":
            len(
                subject_failures
            ),

        "successfully_traced":
            len(
                ok_records
            ),

        "target_missing":
            target_missing,

        "multiple_raw_match":
            multiple_raw_match,
    },

    "differential": {
        "main_lexical_positive":
            main_positive,

        "subject_lexical_zero":
            subject_zero,

        "subject_analyzer_zero":
            subject_analyzer_zero,

        "main_positive_subject_zero":
            main_positive_subject_zero,

        "reference_subject_overlap":
            reference_subject_overlap,

        "production_subject_overlap":
            production_subject_overlap,
    },

    "component_counts":
        dict(
            component_counter
        ),

    "class_census":
        dict(
            class_counter
        ),

    "dominant_class": {
        "class":
            dominant_class,

        "count":
            dominant_count,

        "percent":
            dominant_pct,
    },

    "parity": {
        "engine_main_parity_failures":
            engine_main_parity_failure,

        "subject_wrapper_parity_failures":
            subject_analysis_parity_failure,

        "token_pipeline_mismatches":
            pipeline_mismatch,
    },

    "certification":
        certification,

    "diagnostic_certified":
        certified,

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
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# CONSOLE RESULT
# ============================================================

print("=" * 78)
print(" GENESIS RECALL R4-R9 RESULT")
print("=" * 78)


print()
print("POPULATION")

print(
    "  SUBJECT failures           :",
    len(
        subject_failures
    ),
)

print(
    "  successfully traced        :",
    len(
        ok_records
    ),
    "/221",
)

print(
    "  target raw rows missing    :",
    target_missing,
)

print(
    "  multiple raw matches       :",
    multiple_raw_match,
)


print()
print("PRODUCTION LEXICAL DIFFERENTIAL")

print(
    "  main lexical > 0           :",
    main_positive,
    "/221",
)

print(
    "  subject lexical = 0        :",
    subject_zero,
    "/221",
)

print(
    "  analyze_subject = 0        :",
    subject_analyzer_zero,
    "/221",
)

print(
    "  main > 0 / subject = 0     :",
    main_positive_subject_zero,
    "/221",
)


print()
print("SUBJECT TOKEN OVERLAP")

print(
    "  reference overlap > 0      :",
    reference_subject_overlap,
    "/221",
)

print(
    "  production exact overlap   :",
    production_subject_overlap,
    "/221",
)


print()
print("DIFFERENTIAL COMPONENT CONTRIBUTION")

for name, count in sorted(
    component_counter.items(),
    key=lambda item:
        (
            -item[
                1
            ],
            item[
                0
            ],
        ),
):

    print(
        f"  {name:<44}"
        f"{count:>4}"
    )


print()
print("ROOT-CAUSE CLASS CENSUS")

for name, count in class_counter.most_common():

    pct = (
        100.0
        * count
        / EXPECTED_POPULATION
    )

    print(
        f"  {name:<46}"
        f"{count:>4} "
        f"({pct:6.2f}%)"
    )


print()
print("DOMINANT CLASS")

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


print()
print("PARITY CONTRACTS")

print(
    "  engine/main lexical mismatches :",
    engine_main_parity_failure,
)

print(
    "  subject wrapper mismatches     :",
    subject_analysis_parity_failure,
)

print(
    "  token pipeline mismatches      :",
    pipeline_mismatch,
)


print()
print("CERTIFICATION")

for key, value in certification.items():

    print(
        f"  {key:<36}: {value}"
    )


print()
print(
    "R4-R9 DIAGNOSTIC CERTIFIED :",
    certified,
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
    "class TSV   :",
    CLASS_TSV,
)

print(
    "token TSV   :",
    TOKEN_TSV,
)

print(
    "trace       :",
    TRACE,
)

print(
    "source map  :",
    SOURCE_MAP,
)

print()
print(
    "elapsed seconds:",
    round(
        elapsed,
        2,
    ),
)

print("=" * 78)


raise SystemExit(
    0
    if certified
    else 1
)
