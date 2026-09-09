from __future__ import annotations

import inspect
import sys
from pathlib import Path
from typing import Any

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)

import core.knowledge_catalog.search as search_mod
import core.knowledge_catalog.qualified_search as qualified_mod

from core.retrieval.qualification.evaluator import (
    QualificationEngine,
)


# ============================================================
# Utilities
# ============================================================

def get_value(obj: Any, key: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(key)

    try:
        return getattr(obj, key, None)
    except Exception:
        return None


def doc_id(obj: Any) -> int | None:
    for key in (
        "runtime_document_id",
        "document_id",
        "id",
    ):
        value = get_value(obj, key)

        if value is None:
            continue

        try:
            return int(value)
        except Exception:
            pass

    return None


def print_row(prefix: str, row: Any) -> None:
    print(prefix)
    print("  type       :", type(row))
    print("  id         :", doc_id(row))
    print("  title      :", get_value(row, "title"))
    print("  subject    :", get_value(row, "subject"))
    print("  decision   :", get_value(row, "decision"))
    print("  reason     :", get_value(row, "reason"))
    print("  explanation:", get_value(row, "explanation"))
    print("  confidence :", get_value(row, "confidence"))
    print("  score      :", get_value(row, "score"))


# ============================================================
# A. MODULE / FUNCTION IDENTITY
# ============================================================

print("=" * 78)
print("A. MODULE / FUNCTION IDENTITY")
print("=" * 78)

print()
print("qualified module:")
print("  file :", qualified_mod.__file__)
print("  id   :", id(qualified_mod))

print()
print("search module:")
print("  file :", search_mod.__file__)
print("  id   :", id(search_mod))

print()
print("search_qualified_catalog:")
print("  module :", qualified_mod.search_qualified_catalog.__module__)
print("  id     :", id(qualified_mod.search_qualified_catalog))

print()
print("search_catalog:")
print("  module :", search_mod.search_catalog.__module__)
print("  id     :", id(search_mod.search_catalog))

print()
print("_gate_repair_should_rescue:")
print(
    "  exists :",
    hasattr(
        qualified_mod,
        "_gate_repair_should_rescue",
    ),
)

if hasattr(
    qualified_mod,
    "_gate_repair_should_rescue",
):
    print(
        "  id     :",
        id(
            qualified_mod._gate_repair_should_rescue
        ),
    )


print()
print("_r2_identity_should_rescue:")
print(
    "  exists :",
    hasattr(
        qualified_mod,
        "_r2_identity_should_rescue",
    ),
)


# ============================================================
# B. SEARCH_QUALIFIED_CATALOG GLOBAL BINDINGS
# ============================================================

print()
print("=" * 78)
print("B. SEARCH_QUALIFIED_CATALOG GLOBAL BINDINGS")
print("=" * 78)

fn = qualified_mod.search_qualified_catalog

globals_map = fn.__globals__

for name in (
    "search_catalog",
    "qualify_rows",
    "_gate_repair_should_rescue",
    "_r2_identity_should_rescue",
):
    print()
    print(name)

    if name not in globals_map:
        print("  NOT PRESENT")
        continue

    value = globals_map[name]

    print("  object :", value)
    print("  id     :", id(value))

    try:
        print("  module :", value.__module__)
    except Exception:
        pass


# ============================================================
# C. SOURCE AROUND PRODUCTION RESCUE FLOW
# ============================================================

print()
print("=" * 78)
print("C. SEARCH_QUALIFIED_CATALOG SOURCE")
print("=" * 78)

source = inspect.getsource(
    qualified_mod.search_qualified_catalog
)

for number, line in enumerate(
    source.splitlines(),
    start=1,
):
    if (
        "qualif" in line.lower()
        or "rescue" in line.lower()
        or "reject" in line.lower()
        or "accept" in line.lower()
    ):
        start = max(1, number - 3)
        end = min(
            len(source.splitlines()),
            number + 5,
        )

        lines = source.splitlines()

        print()
        print(
            f"--- local lines {start}-{end} ---"
        )

        for n in range(start, end + 1):
            print(
                f"{n:04d}: {lines[n-1]}"
            )


# ============================================================
# D. BASELINE QUERIES
# ============================================================

CASES = (
    (
        "lane",
        "Edward William Lane Arabic English Lexicon Vol 6",
        86876,
    ),
    (
        "python",
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
)


print()
print("=" * 78)
print("D. RAW + QUALIFIED BASELINE")
print("=" * 78)

for name, query, target in CASES:

    print()
    print("-" * 78)
    print(name)
    print("query  :", query)
    print("target :", target)

    raw = search_mod.search_catalog(
        query,
        db_path=DB,
        limit=100,
    )

    qualified = qualified_mod.search_qualified_catalog(
        query,
        db_path=DB,
        limit=100,
    )

    raw_rank = None
    qualified_rank = None

    raw_target = None
    qualified_target = None

    for rank, row in enumerate(raw, start=1):
        if doc_id(row) == target:
            raw_rank = rank
            raw_target = row
            break

    for rank, row in enumerate(qualified, start=1):
        if doc_id(row) == target:
            qualified_rank = rank
            qualified_target = row
            break

    print("raw count      :", len(raw))
    print("qualified count:", len(qualified))
    print("raw rank       :", raw_rank)
    print("qualified rank :", qualified_rank)

    if raw_target is not None:
        print_row(
            "RAW TARGET:",
            raw_target,
        )

    if qualified_target is not None:
        print_row(
            "QUALIFIED TARGET:",
            qualified_target,
        )


# ============================================================
# E. TRACE PRODUCTION GLOBAL LOOKUP
#
# Patch the function's actual globals dictionary directly.
# This removes ambiguity about module aliases/import references.
# ============================================================

print()
print("=" * 78)
print("E. DIRECT GLOBAL-BINDING TRACE")
print("=" * 78)

events: list[dict[str, Any]] = []

fn_globals = (
    qualified_mod
    .search_qualified_catalog
    .__globals__
)

original_r1f = fn_globals.get(
    "_gate_repair_should_rescue"
)

original_r2 = fn_globals.get(
    "_r2_identity_should_rescue"
)


if original_r1f is None:
    print("FAIL: R1F function absent from production globals")
else:

    def traced_r1f(
        query,
        evidence,
        *,
        threshold,
    ):
        result = original_r1f(
            query,
            evidence,
            threshold=threshold,
        )

        candidate = getattr(
            evidence,
            "candidate",
            None,
        )

        event = {
            "kind": "R1F",
            "query": query,
            "id": doc_id(candidate),
            "title": get_value(
                candidate,
                "title",
            ),
            "result": result,
        }

        events.append(event)

        print()
        print("TRACE R1F")
        print("  query :", query)
        print("  id    :", event["id"])
        print("  title :", event["title"])
        print("  result:", result)

        return result


    fn_globals[
        "_gate_repair_should_rescue"
    ] = traced_r1f


if original_r2 is not None:

    def traced_r2(
        query,
        evidence,
    ):
        result = original_r2(
            query,
            evidence,
        )

        candidate = getattr(
            evidence,
            "candidate",
            None,
        )

        event = {
            "kind": "R2",
            "query": query,
            "id": doc_id(candidate),
            "title": get_value(
                candidate,
                "title",
            ),
            "result": result,
        }

        events.append(event)

        print()
        print("TRACE R2")
        print("  query :", query)
        print("  id    :", event["id"])
        print("  title :", event["title"])
        print("  result:", result)

        return result


    fn_globals[
        "_r2_identity_should_rescue"
    ] = traced_r2


try:

    for name, query, target in CASES:

        print()
        print("-" * 78)
        print("TRACE CASE:", name)

        before = len(events)

        result = (
            qualified_mod
            .search_qualified_catalog(
                query,
                db_path=DB,
                limit=100,
            )
        )

        after = len(events)

        case_events = events[
            before:after
        ]

        target_events = [
            event
            for event in case_events
            if event["id"] == target
        ]

        print()
        print("qualified count :", len(result))
        print("events observed :", len(case_events))
        print("target events   :", len(target_events))

        for event in target_events:
            print(
                "  ",
                event,
            )

finally:

    if original_r1f is not None:
        fn_globals[
            "_gate_repair_should_rescue"
        ] = original_r1f

    if original_r2 is not None:
        fn_globals[
            "_r2_identity_should_rescue"
        ] = original_r2


# ============================================================
# F. QUALIFY_ROWS SIGNATURE + SOURCE
# ============================================================

print()
print("=" * 78)
print("F. QUALIFY_ROWS CONTRACT")
print("=" * 78)

qualify_rows = fn_globals.get(
    "qualify_rows"
)

print("object :", qualify_rows)

if qualify_rows is not None:

    print(
        "signature:",
        inspect.signature(
            qualify_rows
        ),
    )

    try:
        qsource = inspect.getsource(
            qualify_rows
        )

        print()
        print(qsource[:12000])

    except Exception as exc:
        print(
            "source unavailable:",
            repr(exc),
        )


# ============================================================
# G. QUALIFICATION ENGINE
# ============================================================

print()
print("=" * 78)
print("G. QUALIFICATION ENGINE THRESHOLDS")
print("=" * 78)

engine = QualificationEngine()

print(
    "accept             :",
    engine.thresholds.accept,
)
print(
    "minimum_confidence :",
    engine.thresholds.minimum_confidence,
)
print(
    "minimum_lexical    :",
    engine.thresholds.minimum_lexical,
)
print(
    "minimum_subject    :",
    engine.thresholds.minimum_subject,
)
print(
    "minimum_phrase     :",
    engine.thresholds.minimum_phrase,
)


# ============================================================
# H. EVENT SUMMARY
# ============================================================

print()
print("=" * 78)
print("H. EVENT SUMMARY")
print("=" * 78)

print(
    "total rescue calls:",
    len(events),
)

print(
    "R1F calls:",
    sum(
        1
        for event in events
        if event["kind"] == "R1F"
    ),
)

print(
    "R2 calls:",
    sum(
        1
        for event in events
        if event["kind"] == "R2"
    ),
)

print()
print("TARGET EVENT MATRIX")

for name, query, target in CASES:

    matching = [
        event
        for event in events
        if event["id"] == target
    ]

    print(
        f"{name:20}",
        f"id={target:<7}",
        f"events={len(matching)}",
    )

    for event in matching:
        print(
            "   ",
            event["kind"],
            event["result"],
        )


print()
print("=" * 78)
print("R2-R2A-R4-R6 ANATOMY COMPLETE")
print("=" * 78)
