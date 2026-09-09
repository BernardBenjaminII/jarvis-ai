from __future__ import annotations

import ast
import csv
import inspect
import json
import sys
import time

from collections import Counter
from pathlib import Path
from typing import Any, Mapping


PROJECT = Path(
    "/media/abdullah/JARVISDATA/Projects/jarvis-ai"
)

OUTDIR = PROJECT / "artifacts/genesis_recall"

DETAIL_IN = (
    OUTDIR
    / "r4_r10_r3_nine_document_retrieval_anatomy.tsv"
)

REPORT = (
    OUTDIR
    / "r4_r10_r4_candidate_generation_rank_origin.json"
)

DETAIL = (
    OUTDIR
    / "r4_r10_r4_candidate_generation_rank_origin.tsv"
)

CALLS = (
    OUTDIR
    / "r4_r10_r4_search_call_trace.tsv"
)

GENERATOR = (
    OUTDIR
    / "r4_r10_r4_generator_trace.tsv"
)

FINAL_RANK = (
    OUTDIR
    / "r4_r10_r4_final_rank_trace.tsv"
)

TRACE = (
    OUTDIR
    / "r4_r10_r4_candidate_generation_trace.txt"
)

SOURCE_MAP = (
    OUTDIR
    / "r4_r10_r4_search_callgraph_source.txt"
)

SEARCH_FILE = (
    PROJECT
    / "core"
    / "knowledge_catalog"
    / "search.py"
)


sys.path.insert(
    0,
    str(PROJECT),
)


import core.knowledge_catalog.search as search_module

from core.knowledge_catalog.search import (
    search_catalog,
)


EXPECTED = 9


# ============================================================
# HELPERS
# ============================================================

def read_tsv(
    path: Path,
) -> list[dict[str, str]]:

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
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)

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
        writer.writerows(rows)


def row_map(
    raw: Any,
) -> dict[str, Any]:

    if isinstance(
        raw,
        Mapping,
    ):
        return dict(raw)

    if hasattr(
        raw,
        "keys",
    ):
        try:
            return {
                key: raw[key]
                for key in raw.keys()
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
            vars(raw)
        )
    except Exception:
        return {}


def text(
    value: Any,
) -> str:

    if value is None:
        return ""

    return str(
        value
    ).strip()


def first_present(
    row: Mapping[str, Any],
    *names: str,
) -> str:

    lowered = {
        str(k).casefold(): k
        for k in row.keys()
    }

    for name in names:

        key = lowered.get(
            name.casefold()
        )

        if key is None:
            continue

        value = row.get(
            key
        )

        if value not in (
            None,
            "",
        ):
            return text(
                value
            )

    return ""


def identity_equal(
    left: Any,
    right: Any,
) -> bool:

    a = text(left)
    b = text(right)

    if not a or not b:
        return False

    if a.casefold() == b.casefold():
        return True

    try:
        return int(a) == int(b)
    except Exception:
        return False


def raw_document_id(
    raw: Any,
) -> str:

    mapped = row_map(
        raw
    )

    return first_present(
        mapped,
        "document_id",
        "runtime_document_id",
        "doc_id",
    )


def raw_chunk_id(
    raw: Any,
) -> str:

    mapped = row_map(
        raw
    )

    return first_present(
        mapped,
        "chunk_id",
        "source_id",
        "id",
    )


def raw_score_fields(
    raw: Any,
) -> dict[str, Any]:

    mapped = row_map(
        raw
    )

    result = {}

    for key, value in mapped.items():

        low = str(
            key
        ).casefold()

        if (
            "score" in low
            or
            "rank" in low
            or
            "bm25" in low
            or
            "confidence" in low
            or
            "weight" in low
        ):

            result[
                str(key)
            ] = value

    return result


# ============================================================
# STATIC SEARCH CALL GRAPH DISCOVERY
# ============================================================

source = SEARCH_FILE.read_text(
    encoding="utf-8"
)

tree = ast.parse(
    source
)


function_nodes: dict[str, ast.AST] = {}

for node in tree.body:

    if isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        ),
    ):
        function_nodes[
            node.name
        ] = node


search_node = function_nodes.get(
    "search_catalog"
)

if search_node is None:
    raise RuntimeError(
        "search_catalog AST function not found"
    )


def ast_call_name(
    node: ast.Call,
) -> str:

    fn = node.func

    if isinstance(
        fn,
        ast.Name,
    ):
        return fn.id

    if isinstance(
        fn,
        ast.Attribute,
    ):
        parts = []
        cur = fn

        while isinstance(
            cur,
            ast.Attribute,
        ):
            parts.append(
                cur.attr
            )
            cur = cur.value

        if isinstance(
            cur,
            ast.Name,
        ):
            parts.append(
                cur.id
            )

        return ".".join(
            reversed(
                parts
            )
        )

    return ast.dump(
        fn,
        include_attributes=False,
    )


direct_calls = []

for node in ast.walk(
    search_node
):

    if isinstance(
        node,
        ast.Call,
    ):
        direct_calls.append(
            (
                node.lineno,
                ast_call_name(
                    node
                ),
            )
        )


# ============================================================
# DISCOVER MODULE-LOCAL CALLABLES USED BY search_catalog
# ============================================================

module_callables = {}

for _lineno, name in direct_calls:

    root = name.split(
        "."
    )[0]

    if root not in vars(
        search_module
    ):
        continue

    obj = vars(
        search_module
    )[
        root
    ]

    if callable(
        obj
    ):
        module_callables[
            root
        ] = obj


# ============================================================
# TRACE WRAPPERS
# ============================================================

active_case = {
    "case": None,
    "query": None,
    "target_id": None,
}

call_events = []

generator_events = []


def summarize_return(
    value: Any,
    target_id: str,
) -> dict[str, Any]:

    summary = {
        "return_type":
            type(value).__name__,

        "iterable_count":
            "",

        "target_present":
            False,

        "target_rank":
            "",

        "target_chunk_id":
            "",

        "target_scores_json":
            "",
    }


    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):

        summary[
            "iterable_count"
        ] = len(
            value
        )

        for rank, item in enumerate(
            value,
            start=1,
        ):

            if identity_equal(
                raw_document_id(
                    item
                ),
                target_id,
            ):

                summary[
                    "target_present"
                ] = True

                summary[
                    "target_rank"
                ] = rank

                summary[
                    "target_chunk_id"
                ] = raw_chunk_id(
                    item
                )

                summary[
                    "target_scores_json"
                ] = json.dumps(
                    raw_score_fields(
                        item
                    ),
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                )

                break


    return summary


originals = {}


def wrap_function(
    name: str,
    fn: Any,
):

    def wrapper(
        *args,
        **kwargs,
    ):

        case = active_case[
            "case"
        ]

        query = active_case[
            "query"
        ]

        target_id = active_case[
            "target_id"
        ]

        started = time.perf_counter()

        try:

            result = fn(
                *args,
                **kwargs,
            )

            elapsed = (
                time.perf_counter()
                - started
            )

            summary = summarize_return(
                result,
                target_id,
            )

            event = {
                "case":
                    case,

                "query":
                    query,

                "target_id":
                    target_id,

                "callable":
                    name,

                "elapsed_ms":
                    round(
                        elapsed
                        * 1000.0,
                        3,
                    ),

                **summary,
            }

            call_events.append(
                event
            )


            if (
                summary[
                    "iterable_count"
                ]
                != ""
            ):

                generator_events.append(
                    {
                        "case":
                            case,

                        "query":
                            query,

                        "target_id":
                            target_id,

                        "callable":
                            name,

                        "candidate_count":
                            summary[
                                "iterable_count"
                            ],

                        "target_present":
                            summary[
                                "target_present"
                            ],

                        "target_local_rank":
                            summary[
                                "target_rank"
                            ],

                        "target_chunk_id":
                            summary[
                                "target_chunk_id"
                            ],

                        "target_scores_json":
                            summary[
                                "target_scores_json"
                            ],
                    }
                )


            return result


        except Exception:

            elapsed = (
                time.perf_counter()
                - started
            )

            call_events.append(
                {
                    "case":
                        case,

                    "query":
                        query,

                    "target_id":
                        target_id,

                    "callable":
                        name,

                    "elapsed_ms":
                        round(
                            elapsed
                            * 1000.0,
                            3,
                        ),

                    "return_type":
                        "EXCEPTION",
                }
            )

            raise


    wrapper.__name__ = getattr(
        fn,
        "__name__",
        name,
    )

    wrapper.__qualname__ = getattr(
        fn,
        "__qualname__",
        name,
    )

    wrapper.__doc__ = getattr(
        fn,
        "__doc__",
        None,
    )

    return wrapper


# Wrap only module-local callables referenced directly
# by search_catalog. search_catalog itself is not replaced.
for name, fn in module_callables.items():

    if name == "search_catalog":
        continue

    originals[
        name
    ] = fn

    setattr(
        search_module,
        name,
        wrap_function(
            name,
            fn,
        ),
    )


# ============================================================
# LOAD NINE TARGETS
# ============================================================

targets = read_tsv(
    DETAIL_IN
)

if len(
    targets
) != EXPECTED:

    raise RuntimeError(
        f"expected 9 targets, got {len(targets)}"
    )


# ============================================================
# RUN PRODUCTION SEARCH AT FIXED LARGE HORIZON
# ============================================================

detail_rows = []

final_rows = []

trace_lines = []

classification_counter = Counter()

started = time.time()


for index, row in enumerate(
    targets,
    start=1,
):

    query = row[
        "query"
    ]

    target_id = row[
        "document_id"
    ]


    active_case[
        "case"
    ] = index

    active_case[
        "query"
    ] = query

    active_case[
        "target_id"
    ] = target_id


    before_calls = len(
        call_events
    )

    before_generators = len(
        generator_events
    )


    final = list(
        search_module.search_catalog(
            query,
            limit=2000,
        )
    )


    case_calls = call_events[
        before_calls:
    ]

    case_generators = generator_events[
        before_generators:
    ]


    final_rank = None

    final_chunk = ""

    final_scores = {}


    for rank, item in enumerate(
        final,
        start=1,
    ):

        if identity_equal(
            raw_document_id(
                item
            ),
            target_id,
        ):

            final_rank = rank

            final_chunk = raw_chunk_id(
                item
            )

            final_scores = raw_score_fields(
                item
            )

            break


    first_generator = None

    first_generator_rank = None

    first_generator_score = {}

    first_generator_chunk = ""


    for event in case_generators:

        if event.get(
            "target_present"
        ) in (
            True,
            "True",
        ):

            first_generator = event[
                "callable"
            ]

            first_generator_rank = event[
                "target_local_rank"
            ]

            first_generator_chunk = event[
                "target_chunk_id"
            ]

            score_blob = event.get(
                "target_scores_json",
                "",
            )

            if score_blob:

                try:
                    first_generator_score = json.loads(
                        score_blob
                    )
                except Exception:
                    first_generator_score = {}

            break


    # ========================================================
    # CLASSIFICATION
    # ========================================================

    any_generator_target = any(
        event.get(
            "target_present"
        ) in (
            True,
            "True",
        )
        for event in case_generators
    )


    if (
        not any_generator_target
        and
        final_rank is None
    ):

        classification = (
            "CANDIDATE_NOT_GENERATED"
        )


    elif (
        any_generator_target
        and
        final_rank is None
    ):

        classification = (
            "GENERATED_THEN_LOST"
        )


    elif (
        first_generator is not None
        and
        final_rank is not None
        and
        int(
            first_generator_rank
            or 0
        )
        <= 50
        and
        int(
            final_rank
        )
        > 500
    ):

        classification = (
            "POST_GENERATION_RANK_COLLAPSE"
        )


    elif (
        final_rank is not None
        and
        int(
            final_rank
        )
        > 500
    ):

        classification = (
            "SEARCH_RANK_HORIZON_FAILURE"
        )


    elif final_rank is not None:

        classification = (
            "PRODUCTION_SEARCH_EXPOSED_TARGET"
        )


    else:

        classification = (
            "UNCLASSIFIED"
        )


    classification_counter[
        classification
    ] += 1


    detail_rows.append(
        {
            "case":
                index,

            "document_id":
                target_id,

            "query":
                query,

            "r4_r10_r3_diagnosis":
                row[
                    "diagnosis"
                ],

            "first_generator":
                first_generator
                or "",

            "first_generator_rank":
                first_generator_rank
                or "",

            "first_generator_chunk":
                first_generator_chunk,

            "first_generator_scores_json":
                json.dumps(
                    first_generator_score,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                ),

            "generator_target_observed":
                any_generator_target,

            "final_found":
                final_rank
                is not None,

            "final_rank":
                final_rank
                or "",

            "final_chunk_id":
                final_chunk,

            "final_scores_json":
                json.dumps(
                    final_scores,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                ),

            "classification":
                classification,

            "generator_calls":
                len(
                    case_generators
                ),

            "instrumented_calls":
                len(
                    case_calls
                ),
        }
    )


    final_rows.append(
        {
            "case":
                index,

            "document_id":
                target_id,

            "query":
                query,

            "returned":
                len(
                    final
                ),

            "target_found":
                final_rank
                is not None,

            "target_rank":
                final_rank
                or "",

            "target_chunk_id":
                final_chunk,

            "target_scores_json":
                json.dumps(
                    final_scores,
                    ensure_ascii=False,
                    sort_keys=True,
                    default=str,
                ),
        }
    )


    trace_lines.extend(
        (
            "=" * 78,
            f"CASE {index:02d}",
            "=" * 78,
            f"document_id          : {target_id}",
            f"query                : {query}",
            "",
            f"first generator      : {first_generator}",
            f"generator local rank : {first_generator_rank}",
            f"generator chunk      : {first_generator_chunk}",
            f"generator scores     : {first_generator_score}",
            "",
            f"final found          : {final_rank is not None}",
            f"final rank           : {final_rank}",
            f"final chunk          : {final_chunk}",
            f"final scores         : {final_scores}",
            "",
            f"classification       : {classification}",
            "",
            "GENERATOR EVENTS",
        )
    )


    for event in case_generators:

        trace_lines.append(
            "  "
            + json.dumps(
                event,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
        )


    trace_lines.append(
        ""
    )


# ============================================================
# RESTORE MODULE IMMEDIATELY
# ============================================================

for name, fn in originals.items():

    setattr(
        search_module,
        name,
        fn,
    )


# ============================================================
# WRITE CALL GRAPH SOURCE MAP
# ============================================================

source_lines = [
    "=" * 78,
    " GENESIS RECALL R4-R10-R4",
    " search_catalog CALL GRAPH",
    "=" * 78,
    "",
    f"search_catalog lines "
    f"{search_node.lineno}-"
    f"{getattr(search_node, 'end_lineno', search_node.lineno)}",
    "",
    "DIRECT CALLS",
]


for lineno, name in sorted(
    direct_calls
):

    source_lines.append(
        f"{lineno:05d}: {name}"
    )


source_lines.extend(
    (
        "",
        "INSTRUMENTED MODULE-LOCAL CALLABLES",
    )
)


for name in sorted(
    module_callables
):

    obj = module_callables[
        name
    ]

    try:
        sig = inspect.signature(
            obj
        )
    except Exception:
        sig = "<signature unavailable>"

    source_lines.append(
        f"{name} {sig}"
    )


source_lines.extend(
    (
        "",
        "=" * 78,
        "search_catalog SOURCE",
        "=" * 78,
        inspect.getsource(
            search_catalog
        ),
    )
)


SOURCE_MAP.write_text(
    "\n".join(
        source_lines
    )
    + "\n",
    encoding="utf-8",
)


# ============================================================
# ARTIFACTS
# ============================================================

write_tsv(
    DETAIL,
    detail_rows,
)

write_tsv(
    CALLS,
    call_events,
)

write_tsv(
    GENERATOR,
    generator_events,
)

write_tsv(
    FINAL_RANK,
    final_rows,
)


TRACE.write_text(
    "\n".join(
        (
            "=" * 78,
            " GENESIS RECALL R4-R10-R4",
            " EXACT PRODUCTION CANDIDATE-GENERATION TRACE",
            "=" * 78,
            "",
            *trace_lines,
        )
    ),
    encoding="utf-8",
)


# ============================================================
# CERTIFICATION
# ============================================================

all_classified = (
    len(
        detail_rows
    )
    == EXPECTED
)


no_unclassified = (
    classification_counter.get(
        "UNCLASSIFIED",
        0,
    )
    == 0
)


callgraph_captured = (
    len(
        direct_calls
    )
    > 0
)


instrumentation_active = (
    len(
        call_events
    )
    > 0
)


diagnostic_certified = all(
    (
        len(
            targets
        )
        == EXPECTED,

        all_classified,

        no_unclassified,

        callgraph_captured,

        instrumentation_active,
    )
)


elapsed = (
    time.time()
    - started
)


report = {
    "phase":
        "Genesis Recall R4-R10-R4",

    "population": {
        "expected":
            EXPECTED,

        "actual":
            len(
                targets
            ),

        "classified":
            len(
                detail_rows
            ),
    },

    "search_callgraph": {
        "direct_calls":
            len(
                direct_calls
            ),

        "instrumented_module_callables":
            sorted(
                module_callables.keys()
            ),

        "call_events":
            len(
                call_events
            ),

        "generator_events":
            len(
                generator_events
            ),
    },

    "classification_census":
        dict(
            classification_counter
        ),

    "contracts": {
        "all_targets_classified":
            all_classified,

        "no_unclassified":
            no_unclassified,

        "callgraph_captured":
            callgraph_captured,

        "instrumentation_active":
            instrumentation_active,
    },

    "diagnostic_certified":
        diagnostic_certified,

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
print(" GENESIS RECALL R4-R10-R4 RESULT")
print("=" * 78)

print()
print("POPULATION")

print(
    "  expected                     :",
    EXPECTED,
)

print(
    "  actual                       :",
    len(
        targets
    ),
)

print(
    "  classified                   :",
    len(
        detail_rows
    ),
)


print()
print("SEARCH CALL GRAPH")

print(
    "  direct calls                 :",
    len(
        direct_calls
    ),
)

print(
    "  instrumented callables       :",
    len(
        module_callables
    ),
)

print(
    "  call events                  :",
    len(
        call_events
    ),
)

print(
    "  generator events             :",
    len(
        generator_events
    ),
)


print()
print("CLASSIFICATION CENSUS")

for name, count in sorted(
    classification_counter.items(),
    key=lambda item: (
        -item[1],
        item[0],
    ),
):

    print(
        f"  {name:<52} {count}"
    )


print()
print("CERTIFICATION")

print(
    "  all targets classified       :",
    all_classified,
)

print(
    "  no unclassified              :",
    no_unclassified,
)

print(
    "  callgraph captured            :",
    callgraph_captured,
)

print(
    "  instrumentation active        :",
    instrumentation_active,
)


print()
print(
    "R4-R10-R4 DIAGNOSTIC CERTIFIED :",
    diagnostic_certified,
)


print()
print("Artifacts:")
print(" ", REPORT)
print(" ", DETAIL)
print(" ", CALLS)
print(" ", GENERATOR)
print(" ", FINAL_RANK)
print(" ", TRACE)
print(" ", SOURCE_MAP)

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
    if diagnostic_certified
    else 1
)
