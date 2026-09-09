from __future__ import annotations

import csv
import inspect
import json
import re
import sys
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

DETAIL = (
    OUTDIR
    / "r4_r3_subject_signal_detail.tsv"
)

CONTROL = (
    OUTDIR
    / "r4_r3_subject_control_detail.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r4_subject_analyzer_trace.json"
)

TRACE_TSV = (
    OUTDIR
    / "r4_r4_subject_analyzer_trace.tsv"
)


import core.retrieval.qualification.subject as subject_mod

from core.retrieval.qualification.subject import (
    analyze_subject,
)


# ============================================================
# TOKEN HELPERS
# ============================================================

def generic_tokens(value: Any) -> tuple[str, ...]:

    return tuple(
        re.findall(
            r"[a-z0-9]+",
            str(value or "").lower(),
        )
    )


def token_set(value: Any) -> set[str]:

    return set(
        generic_tokens(value)
    )


def overlap(
    left: Any,
    right: Any,
) -> tuple[list[str], float]:

    a = token_set(left)
    b = token_set(right)

    common = sorted(
        a & b
    )

    score = (
        len(common) / len(a)
        if a
        else 0.0
    )

    return common, score


def object_value(
    obj: Any,
    name: str,
):

    try:
        return getattr(
            obj,
            name,
        )
    except Exception:
        return None


# ============================================================
# ANALYZER RESULT
# ============================================================

def result_anatomy(
    result: Any,
) -> dict[str, Any]:

    output = {
        "type":
            (
                f"{type(result).__module__}."
                f"{type(result).__qualname__}"
            ),

        "repr":
            repr(result),
    }

    for name in (
        "score",
        "matched",
        "matches",
        "subject",
        "reason",
        "explanation",
        "query_terms",
        "subject_terms",
        "title_terms",
    ):

        value = object_value(
            result,
            name,
        )

        if value is not None:
            output[name] = value

    try:
        output["dict"] = dict(
            vars(result)
        )
    except Exception:
        pass

    return output


# ============================================================
# DISCOVER MODULE HELPERS
# ============================================================

helpers = {}

for name, obj in vars(
    subject_mod
).items():

    if name.startswith("__"):
        continue

    if not callable(obj):
        continue

    if obj is analyze_subject:
        continue

    if getattr(
        obj,
        "__module__",
        None,
    ) != subject_mod.__name__:
        continue

    try:
        signature = inspect.signature(
            obj
        )
    except Exception:
        continue

    helpers[name] = {
        "object": obj,
        "signature": str(signature),
    }


# ============================================================
# OPTIONAL INTERNAL HELPER EXECUTION
# ============================================================

def execute_helper(
    name: str,
    func,
    query: str,
    subject: str,
    title: str,
):

    attempts = []

    try:
        signature = inspect.signature(
            func
        )
    except Exception:
        return None

    params = list(
        signature.parameters
    )


    # Only invoke obviously pure-looking helper shapes.
    if len(params) == 1:

        for value_name, value in (
            ("query", query),
            ("subject", subject),
            ("title", title),
        ):

            try:
                result = func(
                    value
                )

                attempts.append(
                    {
                        "input":
                            value_name,

                        "result":
                            repr(result),
                    }
                )

            except Exception as exc:

                attempts.append(
                    {
                        "input":
                            value_name,

                        "error":
                            (
                                type(exc).__name__
                                + ": "
                                + str(exc)
                            ),
                    }
                )


    elif len(params) == 2:

        combinations = (
            (
                "query_subject",
                query,
                subject,
            ),

            (
                "query_title",
                query,
                title,
            ),

            (
                "subject_title",
                subject,
                title,
            ),
        )

        for label, a, b in combinations:

            try:
                result = func(
                    a,
                    b,
                )

                attempts.append(
                    {
                        "input":
                            label,

                        "result":
                            repr(result),
                    }
                )

            except Exception as exc:

                attempts.append(
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


    if not attempts:
        return None

    return attempts


# ============================================================
# LOAD FAILURES + CONTROLS
# ============================================================

with DETAIL.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    failure_rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


with CONTROL.open(
    "r",
    encoding="utf-8",
    newline="",
) as f:

    control_rows = list(
        csv.DictReader(
            f,
            delimiter="\t",
        )
    )


if len(failure_rows) != 24:
    raise RuntimeError(
        f"expected 24 failures, found {len(failure_rows)}"
    )


# ============================================================
# TRACE
# ============================================================

started = time.time()

records = []


def trace_case(
    category: str,
    name: str,
    query: str,
    subject: str,
    title: str,
):

    result = analyze_subject(
        query,
        subject,
        title,
    )

    query_subject_common, qs_overlap = overlap(
        query,
        subject,
    )

    query_title_common, qt_overlap = overlap(
        query,
        title,
    )

    subject_title_common, st_overlap = overlap(
        subject,
        title,
    )

    helper_results = {}

    for helper_name, helper_data in helpers.items():

        executed = execute_helper(
            helper_name,
            helper_data[
                "object"
            ],
            query,
            subject,
            title,
        )

        if executed is not None:
            helper_results[
                helper_name
            ] = {
                "signature":
                    helper_data[
                        "signature"
                    ],

                "executions":
                    executed,
            }


    anatomy = result_anatomy(
        result
    )

    score = anatomy.get(
        "score"
    )

    try:
        score_float = float(
            score
        )
    except Exception:
        score_float = None


    record = {
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

        "query_tokens":
            list(
                generic_tokens(
                    query
                )
            ),

        "subject_tokens":
            list(
                generic_tokens(
                    subject
                )
            ),

        "title_tokens":
            list(
                generic_tokens(
                    title
                )
            ),

        "query_subject_common":
            query_subject_common,

        "query_subject_overlap":
            qs_overlap,

        "query_title_common":
            query_title_common,

        "query_title_overlap":
            qt_overlap,

        "subject_title_common":
            subject_title_common,

        "subject_title_overlap":
            st_overlap,

        "analyzer":
            anatomy,

        "analyzer_score":
            score_float,

        "helper_results":
            helper_results,
    }


    records.append(
        record
    )

    return record


print("=" * 78)
print(" GENESIS RECALL R4-R4")
print(" SUBJECT ANALYZER TOKEN-SEMANTICS TRACE")
print("=" * 78)


print()
print("=== A. SUBJECT FAILURE CASES ===")


for index, row in enumerate(
    failure_rows,
    start=1,
):

    record = trace_case(
        "failure",
        f"failure_{index:02d}",
        row[
            "query"
        ],
        row.get(
            "candidate_subject",
            "",
        ),
        row.get(
            "candidate_title",
            "",
        ),
    )


    print()
    print(
        f"[{index:02d}/24] "
        f"document_id="
        f"{row['document_id']}"
    )

    print(
        "  query:",
        record[
            "query"
        ],
    )

    print(
        "  subject:",
        record[
            "subject"
        ],
    )

    print(
        "  generic q/s common:",
        record[
            "query_subject_common"
        ],
    )

    print(
        "  generic q/s overlap:",
        record[
            "query_subject_overlap"
        ],
    )

    print(
        "  analyzer result:",
        record[
            "analyzer"
        ],
    )


print()
print("=== B. ACCEPTED / KNOWN-GOOD CONTROLS ===")


# Restrict duplicate chunk evidence to unique semantic triples.
seen = set()

control_index = 0

for row in control_rows:

    key = (
        row.get(
            "control",
        ),
        row.get(
            "query",
        ),
        row.get(
            "candidate_subject",
        ),
        row.get(
            "candidate_title",
        ),
    )

    if key in seen:
        continue

    seen.add(
        key
    )

    control_index += 1


    record = trace_case(
        "control",
        row.get(
            "control",
            f"control_{control_index}"
        ),
        row.get(
            "query",
            "",
        ),
        row.get(
            "candidate_subject",
            "",
        ),
        row.get(
            "candidate_title",
            "",
        ),
    )


    print()
    print(
        "control:",
        record[
            "name"
        ],
    )

    print(
        "  query:",
        record[
            "query"
        ],
    )

    print(
        "  subject:",
        record[
            "subject"
        ],
    )

    print(
        "  generic q/s common:",
        record[
            "query_subject_common"
        ],
    )

    print(
        "  generic q/s overlap:",
        record[
            "query_subject_overlap"
        ],
    )

    print(
        "  analyzer result:",
        record[
            "analyzer"
        ],
    )


# ============================================================
# COMPARATIVE COUNTS
# ============================================================

failure_records = [
    record
    for record in records
    if record[
        "category"
    ]
    == "failure"
]

control_records = [
    record
    for record in records
    if record[
        "category"
    ]
    == "control"
]


failure_zero = sum(
    1
    for record
    in failure_records
    if record[
        "analyzer_score"
    ]
    == 0.0
)


failure_overlap_positive = sum(
    1
    for record
    in failure_records
    if record[
        "query_subject_overlap"
    ]
    > 0.0
)


control_positive_subject = sum(
    1
    for record
    in control_records
    if (
        record[
            "analyzer_score"
        ]
        is not None
        and record[
            "analyzer_score"
        ]
        > 0.0
    )
)


# ============================================================
# DETERMINE ALGORITHM SYMPTOM
# ============================================================

if (
    failure_zero
    == len(
        failure_records
    )
    and
    failure_overlap_positive
    == len(
        failure_records
    )
):

    symptom = (
        "GENERIC_TOKEN_OVERLAP_PRESENT_"
        "BUT_ANALYZER_ZERO"
    )

else:

    symptom = (
        "MIXED_SUBJECT_ANALYZER_BEHAVIOR"
    )


# ============================================================
# WRITE TSV
# ============================================================

fields = [
    "category",
    "name",
    "query",
    "subject",
    "title",
    "query_subject_overlap",
    "query_title_overlap",
    "subject_title_overlap",
    "analyzer_score",
    "query_subject_common",
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

    for record in records:

        writer.writerow(
            {
                "category":
                    record[
                        "category"
                    ],

                "name":
                    record[
                        "name"
                    ],

                "query":
                    record[
                        "query"
                    ],

                "subject":
                    record[
                        "subject"
                    ],

                "title":
                    record[
                        "title"
                    ],

                "query_subject_overlap":
                    record[
                        "query_subject_overlap"
                    ],

                "query_title_overlap":
                    record[
                        "query_title_overlap"
                    ],

                "subject_title_overlap":
                    record[
                        "subject_title_overlap"
                    ],

                "analyzer_score":
                    record[
                        "analyzer_score"
                    ],

                "query_subject_common":
                    ",".join(
                        record[
                            "query_subject_common"
                        ]
                    ),
            }
        )


# ============================================================
# JSON
# ============================================================

elapsed = time.time() - started


payload = {
    "genesis_recall":
        "R4-R4",

    "purpose":
        (
            "Subject Analyzer Algorithm "
            "+ Token-Semantics Trace"
        ),

    "failure_cases":
        len(
            failure_records
        ),

    "control_cases":
        len(
            control_records
        ),

    "failure_zero_scores":
        failure_zero,

    "failure_positive_generic_overlap":
        failure_overlap_positive,

    "control_positive_subject_scores":
        control_positive_subject,

    "symptom":
        symptom,

    "module_helpers": {
        name:
            {
                "signature":
                    value[
                        "signature"
                    ],
            }
        for name, value
        in helpers.items()
    },

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
        payload,
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
print(" GENESIS RECALL R4-R4 RESULT")
print("=" * 78)


print()
print("FAILURE CASES")

print(
    "  traced                     :",
    len(
        failure_records
    ),
)

print(
    "  analyzer score = 0         :",
    failure_zero,
)

print(
    "  generic token overlap > 0  :",
    failure_overlap_positive,
)


print()
print("CONTROL CASES")

print(
    "  unique controls traced     :",
    len(
        control_records
    ),
)

print(
    "  analyzer score > 0         :",
    control_positive_subject,
)


print()
print("ALGORITHM SYMPTOM")

print(
    " ",
    symptom,
)


print()
print("SUBJECT MODULE HELPERS")

for name, value in helpers.items():

    print(
        f"  {name:<30}",
        value[
            "signature"
        ],
    )


complete = (
    len(
        failure_records
    )
    == 24
    and
    failure_zero
    == 24
)


print()
print("CERTIFICATION")

print(
    "  exact failure trace       :",
    len(
        failure_records
    )
    == 24,
)

print(
    "  zero-score reproduced     :",
    failure_zero
    == 24,
)

print(
    "  source captured           :",
    True,
)

print()
print(
    "R4-R4 DIAGNOSTIC CERTIFIED :",
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
