from __future__ import annotations

import csv
import inspect
import json
import re
import time

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

INPUT_JSON = (
    OUTDIR
    / "r4_r4_subject_analyzer_trace.json"
)

REPORT = (
    OUTDIR
    / "r4_r5_lexical_zero_score_anatomy.json"
)

TRACE_TSV = (
    OUTDIR
    / "r4_r5_lexical_zero_score_anatomy.tsv"
)


import core.retrieval.qualification.subject as subject_mod


analyze_lexical = (
    subject_mod.analyze_lexical
)

lexical_module = inspect.getmodule(
    analyze_lexical
)

if lexical_module is None:
    raise RuntimeError(
        "unable to locate lexical module"
    )


# ============================================================
# GENERIC REFERENCE TOKENIZATION
# ============================================================

def generic_tokens(
    value: Any,
) -> tuple[str, ...]:

    return tuple(
        re.findall(
            r"[a-z0-9]+",
            str(value or "").lower(),
        )
    )


def unique_tokens(
    value: Any,
) -> set[str]:

    return set(
        generic_tokens(
            value
        )
    )


def generic_overlap(
    query: Any,
    candidate: Any,
) -> dict[str, Any]:

    q = unique_tokens(
        query
    )

    c = unique_tokens(
        candidate
    )

    common = sorted(
        q & c
    )

    missing = sorted(
        q - c
    )

    extra = sorted(
        c - q
    )

    return {
        "query_tokens":
            sorted(q),

        "candidate_tokens":
            sorted(c),

        "common":
            common,

        "missing_query_tokens":
            missing,

        "extra_candidate_tokens":
            extra,

        "matched_query_fraction":
            (
                len(common)
                / len(q)
                if q
                else 0.0
            ),
    }


# ============================================================
# SAFE RESULT ANATOMY
# ============================================================

def anatomy(
    value: Any,
) -> dict[str, Any]:

    output = {
        "type":
            (
                f"{type(value).__module__}."
                f"{type(value).__qualname__}"
            ),

        "repr":
            repr(value),
    }

    try:
        output["dict"] = dict(
            vars(value)
        )
    except Exception:
        pass

    for name in (
        "score",
        "query_tokens",
        "candidate_tokens",
        "matched_tokens",
        "matches",
        "overlap",
        "coverage",
        "query",
        "candidate",
        "text",
        "normalized_query",
        "normalized_candidate",
        "reason",
        "explanation",
    ):

        try:
            item = getattr(
                value,
                name,
            )
        except Exception:
            continue

        try:
            json.dumps(
                item,
                default=str,
            )

            output[name] = item

        except Exception:
            output[name] = repr(
                item
            )

    return output


def score_of(
    value: Any,
) -> float | None:

    try:
        return float(
            getattr(
                value,
                "score",
            )
        )
    except Exception:
        return None


# ============================================================
# DISCOVER INTERNAL LEXICAL HELPERS
# ============================================================

helpers = {}

for name, obj in vars(
    lexical_module
).items():

    if name.startswith("__"):
        continue

    if obj is analyze_lexical:
        continue

    if not callable(obj):
        continue

    if getattr(
        obj,
        "__module__",
        None,
    ) != lexical_module.__name__:
        continue

    try:
        signature = inspect.signature(
            obj
        )
    except Exception:
        continue

    helpers[name] = {
        "object":
            obj,

        "signature":
            str(signature),
    }


# ============================================================
# CONSERVATIVE HELPER EXECUTION
#
# Only invoke simple one-argument functions that appear to be
# normalizers/tokenizers, and simple two-argument functions
# that appear lexical/matching-related.
# ============================================================

SAFE_NAME_HINTS = (
    "token",
    "normal",
    "term",
    "word",
    "lex",
    "overlap",
    "match",
    "score",
    "clean",
)


def helper_is_interesting(
    name: str,
) -> bool:

    lower = name.lower()

    return any(
        hint in lower
        for hint in SAFE_NAME_HINTS
    )


def execute_helpers(
    query: str,
    candidate: str,
) -> dict[str, Any]:

    results = {}

    for name, meta in helpers.items():

        if not helper_is_interesting(
            name
        ):
            continue

        func = meta[
            "object"
        ]

        try:
            sig = inspect.signature(
                func
            )
        except Exception:
            continue

        params = list(
            sig.parameters.values()
        )

        # Skip methods requiring variadic or obviously complex shapes.
        if any(
            p.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
            for p in params
        ):
            continue

        executions = []


        if len(params) == 1:

            for label, value in (
                ("query", query),
                ("candidate", candidate),
            ):

                try:
                    result = func(
                        value
                    )

                    executions.append(
                        {
                            "input":
                                label,

                            "result":
                                repr(result),
                        }
                    )

                except Exception as exc:

                    executions.append(
                        {
                            "input":
                                label,

                            "error":
                                (
                                    type(exc).__name__
                                    + ": "
                                    + str(exc)
                                ),
                        }
                    )


        elif len(params) == 2:

            try:
                result = func(
                    query,
                    candidate,
                )

                executions.append(
                    {
                        "input":
                            "query_candidate",

                        "result":
                            repr(result),
                    }
                )

            except Exception as exc:

                executions.append(
                    {
                        "input":
                            "query_candidate",

                        "error":
                            (
                                type(exc).__name__
                                + ": "
                                + str(exc)
                            ),
                    }
                )


        if executions:

            results[
                name
            ] = {
                "signature":
                    meta[
                        "signature"
                    ],

                "executions":
                    executions,
            }

    return results


# ============================================================
# LOAD R4-R4 CASES
# ============================================================

payload = json.loads(
    INPUT_JSON.read_text(
        encoding="utf-8"
    )
)

input_records = payload[
    "records"
]


failure_input = [
    row
    for row in input_records
    if row[
        "category"
    ]
    == "failure"
]

control_input = [
    row
    for row in input_records
    if row[
        "category"
    ]
    == "control"
]


if len(
    failure_input
) != 24:

    raise RuntimeError(
        "R4-R5 requires exact "
        "24-case R4-R4 failure sample"
    )


# ============================================================
# TRACE
# ============================================================

started = time.time()

records = []


def run_form(
    category: str,
    name: str,
    query: str,
    subject: str,
    title: str,
    form_name: str,
    candidate_text: str,
) -> dict[str, Any]:

    result = analyze_lexical(
        query,
        candidate_text,
    )

    record = {
        "category":
            category,

        "name":
            name,

        "form":
            form_name,

        "query":
            query,

        "subject":
            subject,

        "title":
            title,

        "candidate_text":
            candidate_text,

        "generic":
            generic_overlap(
                query,
                candidate_text,
            ),

        "lexical_result":
            anatomy(
                result
            ),

        "lexical_score":
            score_of(
                result
            ),

        "internal_helpers":
            execute_helpers(
                query,
                candidate_text,
            ),
    }

    records.append(
        record
    )

    return record


def trace_input(
    row: dict[str, Any],
):

    category = str(
        row.get(
            "category",
            "",
        )
    )

    name = str(
        row.get(
            "name",
            "",
        )
    )

    query = str(
        row.get(
            "query",
            "",
        )
        or ""
    )

    subject = str(
        row.get(
            "subject",
            "",
        )
        or ""
    )

    title = str(
        row.get(
            "title",
            "",
        )
        or ""
    )

    combined = " ".join(
        x
        for x in (
            subject,
            title,
        )
        if x
    )


    subject_result = run_form(
        category,
        name,
        query,
        subject,
        title,
        "SUBJECT_ONLY",
        subject,
    )

    title_result = run_form(
        category,
        name,
        query,
        subject,
        title,
        "TITLE_ONLY",
        title,
    )

    combined_result = run_form(
        category,
        name,
        query,
        subject,
        title,
        "SUBJECT_PLUS_TITLE",
        combined,
    )


    return {
        "category":
            category,

        "name":
            name,

        "query":
            query,

        "subject":
            subject,

        "title":
            title,

        "subject_equals_title":
            subject == title,

        "scores": {
            "subject_only":
                subject_result[
                    "lexical_score"
                ],

            "title_only":
                title_result[
                    "lexical_score"
                ],

            "subject_plus_title":
                combined_result[
                    "lexical_score"
                ],
        },
    }


print("=" * 78)
print(" GENESIS RECALL R4-R5")
print(" LEXICAL ZERO-SCORE ROOT-CAUSE ANATOMY")
print("=" * 78)


case_summaries = []


print()
print("=== A. 24 SUBJECT-FAILURE CASES ===")


for index, row in enumerate(
    failure_input,
    start=1,
):

    summary = trace_input(
        row
    )

    case_summaries.append(
        summary
    )

    print()
    print(
        f"[{index:02d}/24]",
        summary[
            "name"
        ],
    )

    print(
        "  query:",
        summary[
            "query"
        ],
    )

    print(
        "  subject == title:",
        summary[
            "subject_equals_title"
        ],
    )

    print(
        "  subject-only score :",
        summary[
            "scores"
        ][
            "subject_only"
        ],
    )

    print(
        "  title-only score   :",
        summary[
            "scores"
        ][
            "title_only"
        ],
    )

    print(
        "  combined score     :",
        summary[
            "scores"
        ][
            "subject_plus_title"
        ],
    )


print()
print("=== B. ACCEPTED CONTROLS ===")


for row in control_input:

    summary = trace_input(
        row
    )

    case_summaries.append(
        summary
    )

    print()
    print(
        "control:",
        summary[
            "name"
        ],
    )

    print(
        "  subject-only score :",
        summary[
            "scores"
        ][
            "subject_only"
        ],
    )

    print(
        "  title-only score   :",
        summary[
            "scores"
        ][
            "title_only"
        ],
    )

    print(
        "  combined score     :",
        summary[
            "scores"
        ][
            "subject_plus_title"
        ],
    )


# ============================================================
# FAILURE STATISTICS
# ============================================================

failure_summaries = [
    row
    for row in case_summaries
    if row[
        "category"
    ]
    == "failure"
]


def count_score(
    key: str,
    predicate,
) -> int:

    total = 0

    for row in failure_summaries:

        value = row[
            "scores"
        ][
            key
        ]

        if predicate(
            value
        ):
            total += 1

    return total


subject_zero = count_score(
    "subject_only",
    lambda x:
        x == 0.0,
)

title_zero = count_score(
    "title_only",
    lambda x:
        x == 0.0,
)

combined_zero = count_score(
    "subject_plus_title",
    lambda x:
        x == 0.0,
)


subject_positive = count_score(
    "subject_only",
    lambda x:
        x is not None
        and x > 0.0,
)

title_positive = count_score(
    "title_only",
    lambda x:
        x is not None
        and x > 0.0,
)

combined_positive = count_score(
    "subject_plus_title",
    lambda x:
        x is not None
        and x > 0.0,
)


duplication_changes_score = sum(
    1
    for row in failure_summaries
    if (
        row[
            "scores"
        ][
            "subject_only"
        ]
        !=
        row[
            "scores"
        ][
            "subject_plus_title"
        ]
    )
)


# ============================================================
# GENERIC OVERLAP VS PRODUCTION LEXICAL
# ============================================================

failure_combined_records = [
    row
    for row in records
    if (
        row[
            "category"
        ]
        == "failure"
        and
        row[
            "form"
        ]
        == "SUBJECT_PLUS_TITLE"
    )
]


generic_overlap_positive = sum(
    1
    for row in failure_combined_records
    if (
        row[
            "generic"
        ][
            "matched_query_fraction"
        ]
        > 0.0
    )
)


lexical_zero_despite_overlap = sum(
    1
    for row in failure_combined_records
    if (
        row[
            "generic"
        ][
            "matched_query_fraction"
        ]
        > 0.0
        and
        row[
            "lexical_score"
        ]
        == 0.0
    )
)


# ============================================================
# CLASSIFY ROOT-CAUSE LOCATION
# ============================================================

if (
    subject_zero == 24
    and
    title_zero == 24
    and
    combined_zero == 24
    and
    lexical_zero_despite_overlap == 24
):

    root_class = (
        "LEXICAL_ANALYZER_TOKEN_OR_MATCH_SEMANTICS"
    )

elif (
    subject_positive > 0
    and
    combined_zero > 0
):

    root_class = (
        "SUBJECT_TITLE_COMBINATION_OR_DUPLICATION_EFFECT"
    )

elif (
    subject_zero == 24
    and
    title_zero == 24
    and
    combined_positive > 0
):

    root_class = (
        "COMBINED_TEXT_REQUIRED_FOR_LEXICAL_MATCH"
    )

else:

    root_class = (
        "MIXED_LEXICAL_BEHAVIOR"
    )


# ============================================================
# WRITE TRACE TSV
# ============================================================

fields = [
    "category",
    "name",
    "form",
    "query",
    "candidate_text",
    "lexical_score",
    "matched_query_fraction",
    "common_tokens",
    "missing_query_tokens",
]


with TRACE_TSV.open(
    "w",
    encoding="utf-8",
    newline="",
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=fields,
        delimiter="\t",
    )

    writer.writeheader()

    for row in records:

        writer.writerow(
            {
                "category":
                    row[
                        "category"
                    ],

                "name":
                    row[
                        "name"
                    ],

                "form":
                    row[
                        "form"
                    ],

                "query":
                    row[
                        "query"
                    ],

                "candidate_text":
                    row[
                        "candidate_text"
                    ],

                "lexical_score":
                    row[
                        "lexical_score"
                    ],

                "matched_query_fraction":
                    row[
                        "generic"
                    ][
                        "matched_query_fraction"
                    ],

                "common_tokens":
                    ",".join(
                        row[
                            "generic"
                        ][
                            "common"
                        ]
                    ),

                "missing_query_tokens":
                    ",".join(
                        row[
                            "generic"
                        ][
                            "missing_query_tokens"
                        ]
                    ),
            }
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
        "R4-R5",

    "purpose":
        (
            "Lexical Analyzer Normalization, "
            "Tokenization & Zero-Score Root-Cause Anatomy"
        ),

    "population": {
        "failure_cases":
            len(
                failure_summaries
            ),

        "control_cases":
            len(
                control_input
            ),

        "forms_per_case":
            3,
    },

    "failure_scores": {
        "subject_only_zero":
            subject_zero,

        "title_only_zero":
            title_zero,

        "combined_zero":
            combined_zero,

        "subject_only_positive":
            subject_positive,

        "title_only_positive":
            title_positive,

        "combined_positive":
            combined_positive,

        "duplication_changes_score":
            duplication_changes_score,
    },

    "overlap_comparison": {
        "generic_overlap_positive":
            generic_overlap_positive,

        "lexical_zero_despite_overlap":
            lexical_zero_despite_overlap,
    },

    "root_cause_class":
        root_class,

    "lexical_module": {
        "name":
            lexical_module.__name__,

        "file":
            inspect.getsourcefile(
                analyze_lexical
            ),

        "analyze_lexical_signature":
            str(
                inspect.signature(
                    analyze_lexical
                )
            ),

        "helpers": {
            name: {
                "signature":
                    value[
                        "signature"
                    ]
            }
            for name, value
            in helpers.items()
        },
    },

    "case_summaries":
        case_summaries,

    "records":
        records,

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
# SUMMARY
# ============================================================

print()
print("=" * 78)
print(" GENESIS RECALL R4-R5 RESULT")
print("=" * 78)


print()
print("FAILURE POPULATION")

print(
    "  traced                    :",
    len(
        failure_summaries
    ),
)


print()
print("LEXICAL SCORE BY INPUT FORM")

print(
    "  subject only = 0          :",
    subject_zero,
    "/24",
)

print(
    "  title only = 0            :",
    title_zero,
    "/24",
)

print(
    "  subject + title = 0       :",
    combined_zero,
    "/24",
)

print(
    "  duplication changes score :",
    duplication_changes_score,
    "/24",
)


print()
print("REFERENCE TOKEN OVERLAP")

print(
    "  generic overlap > 0       :",
    generic_overlap_positive,
    "/24",
)

print(
    "  overlap but lexical=0     :",
    lexical_zero_despite_overlap,
    "/24",
)


print()
print("ROOT-CAUSE CLASS")

print(
    " ",
    root_class,
)


print()
print("LEXICAL IMPLEMENTATION")

print(
    "  module :",
    lexical_module.__name__,
)

print(
    "  file   :",
    inspect.getsourcefile(
        analyze_lexical
    ),
)

print(
    "  call   :",
    inspect.signature(
        analyze_lexical
    ),
)


print()
print("DISCOVERED INTERNAL HELPERS")

if helpers:

    for name, meta in helpers.items():

        print(
            f"  {name:<32}",
            meta[
                "signature"
            ],
        )

else:

    print(
        "  NONE"
    )


complete = (
    len(
        failure_summaries
    )
    == 24
    and
    len(
        failure_combined_records
    )
    == 24
)


print()
print("CERTIFICATION")

print(
    "  exact failure population  :",
    len(
        failure_summaries
    )
    == 24,
)

print(
    "  all three forms traced    :",
    len(
        failure_combined_records
    )
    == 24,
)

print(
    "  lexical source resolved   :",
    lexical_module is not None,
)

print()
print(
    "R4-R5 DIAGNOSTIC CERTIFIED :",
    complete,
)


print()
print(
    "JSON report:",
    REPORT,
)

print(
    "trace TSV  :",
    TRACE_TSV,
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
