#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
PYTHON="/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python"

TARGET="$ROOT/core/knowledge_catalog/qualified_search.py"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.knowledge_backups/query_normalization_r1_1_${STAMP}"

echo "======================================================================"
echo " GENESIS KNOWLEDGE RETRIEVAL"
echo " R1.1 — CONVERSATIONAL QUERY NORMALIZATION"
echo "======================================================================"

cd "$ROOT"

[[ -f "$TARGET" ]] || {
    echo "FAIL: missing target:"
    echo "  $TARGET"
    exit 1
}

grep -q 'GENESIS_QUALIFICATION_GATE_REPAIR_R1' "$TARGET" || {
    echo "FAIL: Qualification Gate Repair R1 is not installed."
    echo "R1.1 expects R1 as its baseline."
    exit 1
}

mkdir -p "$BACKUP"
cp -a "$TARGET" "$BACKUP/qualified_search.py"

echo
echo "Backup:"
echo "  $BACKUP"

"$PYTHON" - "$TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()

MARKER = "# GENESIS_CONVERSATIONAL_QUERY_NORMALIZATION_R1_1"

if MARKER in source:
    print("R1.1 already installed; no duplicate patch applied.")
    raise SystemExit(0)

# ----------------------------------------------------------------------
# Locate R1 search_qualified_catalog.
# ----------------------------------------------------------------------

start_marker = '''def search_qualified_catalog(
    query: str,
    *,
    db_path: Path = DEFAULT_CATALOG_DB,
    limit: int = 25,
    engine: QualificationEngine | None = None,
) -> list[dict[str, Any]]:
'''

start = source.find(start_marker)

if start < 0:
    raise SystemExit(
        "FAIL: could not locate R1 search_qualified_catalog(). "
        "No changes made."
    )

# Find the next top-level function/class after this function.
search_from = start + len(start_marker)

candidates = []

for token in (
    "\ndef ",
    "\nclass ",
):
    pos = source.find(token, search_from)
    if pos >= 0:
        candidates.append(pos + 1)

end = min(candidates) if candidates else len(source)

old_function = source[start:end]

if "raw_limit = max(" not in old_function:
    raise SystemExit(
        "FAIL: located search_qualified_catalog() does not look like R1. "
        "No changes made."
    )

if "_gate_repair_should_rescue" not in old_function:
    raise SystemExit(
        "FAIL: R1 rescue path not found in search_qualified_catalog(). "
        "No changes made."
    )

replacement = r'''# GENESIS_CONVERSATIONAL_QUERY_NORMALIZATION_R1_1
#
# R1.1 principle:
#
# The Executive may receive natural conversational questions while the
# catalog retrieval layer performs best on compact topical queries.
#
# R1.1 therefore:
#
#   1. preserves the original operator query;
#   2. derives a conservative normalized retrieval variant;
#   3. searches BOTH forms when they differ;
#   4. merges and deduplicates the candidate pools;
#   5. qualifies against the normalized topical query;
#   6. preserves R1's conservative content rescue;
#   7. records the transformation in the qualification trace.
#
# It does NOT perform global stopword deletion and does NOT rewrite
# arbitrary queries.

_CONVERSATIONAL_QUERY_PATTERNS = (
    # "Do you have ..."
    r"^\s*do\s+you\s+have\s+(?:any\s+)?information\s+(?:on|about)\s+",
    r"^\s*do\s+you\s+have\s+(?:anything|something)\s+(?:on|about)\s+",

    # "Do I have ..."
    r"^\s*do\s+i\s+have\s+(?:any\s+)?information\s+(?:on|about)\s+",
    r"^\s*do\s+i\s+have\s+(?:anything|something)\s+(?:on|about)\s+",

    # "Tell me ..."
    r"^\s*(?:please\s+)?tell\s+me\s+(?:something\s+)?about\s+",

    # "What do you know ..."
    r"^\s*what\s+do\s+you\s+know\s+(?:about|on)\s+",

    # "Can/Could you find ..."
    r"^\s*(?:can|could|would)\s+you\s+(?:please\s+)?find\s+"
    r"(?:me\s+)?(?:any\s+)?information\s+(?:on|about)\s+",

    # "Find information ..."
    r"^\s*(?:please\s+)?find\s+(?:me\s+)?(?:any\s+)?information\s+"
    r"(?:on|about)\s+",

    # "Show me ..."
    r"^\s*(?:please\s+)?show\s+me\s+(?:any\s+)?information\s+"
    r"(?:on|about)\s+",

    r"^\s*(?:please\s+)?show\s+me\s+(?:anything|something)\s+"
    r"(?:on|about)\s+",
)


def normalize_conversational_query(query: str) -> str:
    """
    Remove only recognized conversational retrieval scaffolding.

    This intentionally does NOT apply general stopword removal.

    Examples:
        Do you have any information on urban warfare?
            -> urban warfare

        Tell me about urban warfare.
            -> urban warfare

        What do you know about HTTP?
            -> HTTP

        What does RFC 9110 define?
            -> unchanged

        The Art of War
            -> unchanged
    """
    import re

    original = str(query or "").strip()

    if not original:
        return original

    normalized = original

    for pattern in _CONVERSATIONAL_QUERY_PATTERNS:
        candidate = re.sub(
            pattern,
            "",
            normalized,
            count=1,
            flags=re.IGNORECASE,
        ).strip()

        if candidate != normalized:
            normalized = candidate
            break

    # Strip punctuation introduced by the conversational wrapper while
    # preserving useful search syntax inside the actual subject.
    normalized = normalized.strip()

    normalized = re.sub(
        r"^[\s:;,]+",
        "",
        normalized,
    )

    normalized = re.sub(
        r"[\s?!.,;:]+$",
        "",
        normalized,
    )

    # Never normalize a meaningful query into nothing.
    if not normalized:
        return original

    return normalized


def _r1_1_row_identity(row: Any) -> tuple[str, str, str]:
    """
    Stable candidate identity for merging original-query and
    normalized-query retrieval.
    """
    data = dict(row)

    path = str(
        data.get("file_path")
        or data.get("source_path")
        or ""
    )

    excerpt = str(
        data.get("excerpt")
        or data.get("chunk_text")
        or ""
    )

    source_id = str(
        data.get("source_id")
        or data.get("chunk_id")
        or data.get("id")
        or ""
    )

    return (
        path,
        source_id,
        excerpt,
    )


def _r1_1_merge_rows(
    *groups: Any,
) -> list[Any]:
    merged: list[Any] = []
    seen: set[tuple[str, str, str]] = set()

    for group in groups:
        for row in group:
            identity = _r1_1_row_identity(row)

            if identity in seen:
                continue

            seen.add(identity)
            merged.append(row)

    return merged


def search_qualified_catalog(
    query: str,
    *,
    db_path: Path = DEFAULT_CATALOG_DB,
    limit: int = 25,
    engine: QualificationEngine | None = None,
) -> list[dict[str, Any]]:
    requested_limit = max(1, int(limit))

    raw_limit = max(
        requested_limit * 4,
        100,
    )

    original_query = str(query or "").strip()

    normalized_query = normalize_conversational_query(
        original_query
    )

    normalization_applied = (
        bool(normalized_query)
        and normalized_query != original_query
    )

    # --------------------------------------------------------------
    # Search original query.
    #
    # We preserve this because the complete wording can occasionally
    # contain useful identifiers or specificity.
    # --------------------------------------------------------------

    original_rows = list(
        search_catalog(
            original_query,
            db_path=db_path,
            limit=raw_limit,
        )
    )

    # --------------------------------------------------------------
    # Search normalized topical query when applicable.
    # --------------------------------------------------------------

    if normalization_applied:
        normalized_rows = list(
            search_catalog(
                normalized_query,
                db_path=db_path,
                limit=raw_limit,
            )
        )
    else:
        normalized_rows = []

    raw_rows = _r1_1_merge_rows(
        normalized_rows,
        original_rows,
    )

    # --------------------------------------------------------------
    # Qualification query
    #
    # Qualification should judge candidate relevance against the
    # actual topical request, not conversational scaffolding.
    # --------------------------------------------------------------

    qualification_query = (
        normalized_query
        if normalization_applied
        else original_query
    )

    accepted_rows, result = qualify_rows(
        qualification_query,
        raw_rows,
        engine=engine,
    )

    output = list(accepted_rows)

    seen: set[tuple[str, str]] = set()

    for row in output:
        path_value = str(
            row.get("file_path")
            or row.get("source_path")
            or ""
        )

        excerpt_value = str(
            row.get("excerpt")
            or row.get("chunk_text")
            or ""
        )

        seen.add(
            (
                path_value,
                excerpt_value,
            )
        )

    rescue_diagnostics: list[dict[str, Any]] = []

    # --------------------------------------------------------------
    # Preserve Qualification Gate Repair R1.
    # --------------------------------------------------------------

    if len(output) < requested_limit:

        for rejected in result.rejected:

            rescue, reason = _gate_repair_should_rescue(
                qualification_query,
                rejected,
                threshold=float(result.threshold),
            )

            rescue_diagnostics.append(
                {
                    "source_id":
                        rejected.candidate.source_id,

                    "source_path":
                        rejected.candidate.source_path,

                    "rescue":
                        rescue,

                    "reason":
                        reason,

                    "score":
                        rejected.score.to_dict(),

                    "original_decision":
                        rejected.decision.value,
                }
            )

            if not rescue:
                continue

            row = _gate_repair_qualified_row(
                rejected,
                reason=reason,
            )

            path_value = str(
                row.get("file_path")
                or row.get("source_path")
                or ""
            )

            excerpt_value = str(
                row.get("excerpt")
                or row.get("chunk_text")
                or ""
            )

            identity = (
                path_value,
                excerpt_value,
            )

            if identity in seen:
                continue

            seen.add(identity)

            row["query_original"] = original_query
            row["query_normalized"] = normalized_query
            row["query_normalization_applied"] = (
                normalization_applied
            )

            output.append(row)

            if len(output) >= requested_limit:
                break

    # --------------------------------------------------------------
    # Add normalization provenance to normally accepted rows too.
    # --------------------------------------------------------------

    for row in output:
        row.setdefault(
            "query_original",
            original_query,
        )

        row.setdefault(
            "query_normalized",
            normalized_query,
        )

        row.setdefault(
            "query_normalization_applied",
            normalization_applied,
        )

    # --------------------------------------------------------------
    # Preserve and augment trace.
    # --------------------------------------------------------------

    trace = get_last_qualification_trace()

    if trace is not None:
        trace["gate_repair_revision"] = "R1"
        trace["query_normalization_revision"] = "R1.1"

        trace["query_original"] = original_query
        trace["query_normalized"] = normalized_query

        trace["query_normalization_applied"] = (
            normalization_applied
        )

        trace["qualification_query"] = (
            qualification_query
        )

        trace["raw_candidate_limit"] = raw_limit

        trace["raw_original_count"] = len(
            original_rows
        )

        trace["raw_normalized_count"] = len(
            normalized_rows
        )

        trace["raw_merged_count"] = len(
            raw_rows
        )

        trace["requested_limit"] = requested_limit

        trace["rescued_count"] = sum(
            1
            for item in output
            if item.get("qualification_rescue")
        )

        trace["returned_count"] = len(output)

        trace["rescue_diagnostics"] = (
            rescue_diagnostics
        )

        _LAST_TRACE.set(trace)

    return output[:requested_limit]
'''

updated = (
    source[:start]
    + replacement
    + source[end:]
)

path.write_text(updated)

print("PATCHED:", path)
PY


# ======================================================================
# SOURCE CERTIFICATION
# ======================================================================

echo
echo "======================================================================"
echo " SOURCE CERTIFICATION"
echo "======================================================================"

"$PYTHON" -m py_compile "$TARGET"

echo "PASS: Python syntax"

"$PYTHON" - <<'PY'
from core.knowledge_catalog.qualified_search import (
    normalize_conversational_query,
    search_qualified_catalog,
    get_last_qualification_trace,
)

assert callable(normalize_conversational_query)
assert callable(search_qualified_catalog)
assert callable(get_last_qualification_trace)

print("PASS: R1.1 imports")
PY


# ======================================================================
# NORMALIZER UNIT CERTIFICATION
# ======================================================================

echo
echo "======================================================================"
echo " NORMALIZER CERTIFICATION"
echo "======================================================================"

"$PYTHON" - <<'PY'
from core.knowledge_catalog.qualified_search import (
    normalize_conversational_query,
)

CASES = {
    "Do you have any information on urban warfare?":
        "urban warfare",

    "Do you have anything about urban warfare?":
        "urban warfare",

    "Do I have anything about helicopter aerodynamics?":
        "helicopter aerodynamics",

    "Tell me about urban warfare.":
        "urban warfare",

    "Please tell me about urban warfare.":
        "urban warfare",

    "What do you know about HTTP?":
        "HTTP",

    "Can you find information about urban warfare?":
        "urban warfare",

    "Could you please find me information on urban warfare?":
        "urban warfare",

    "Show me information on urban warfare.":
        "urban warfare",

    # These MUST remain semantically intact.
    "What does RFC 9110 define?":
        "What does RFC 9110 define?",

    "What is C++?":
        "What is C++?",

    "The Art of War":
        "The Art of War",

    "War and Peace":
        "War and Peace",

    '"urban warfare"':
        '"urban warfare"',
}

failures = []

for original, expected in CASES.items():

    actual = normalize_conversational_query(
        original
    )

    status = (
        "PASS"
        if actual == expected
        else "FAIL"
    )

    print(
        f"{status:<5} "
        f"{original!r:<62} -> {actual!r}"
    )

    if actual != expected:
        failures.append(
            (
                original,
                expected,
                actual,
            )
        )

if failures:
    print()
    print("NORMALIZER FAILURES:")

    for original, expected, actual in failures:
        print()
        print(" original:", repr(original))
        print(" expected:", repr(expected))
        print(" actual  :", repr(actual))

    raise SystemExit(1)

print()
print("PASS: deterministic normalizer")
PY


# ======================================================================
# RETRIEVAL REGRESSION CERTIFICATION
# ======================================================================

echo
echo "======================================================================"
echo " R1.1 RETRIEVAL REGRESSION CERTIFICATION"
echo "======================================================================"

"$PYTHON" - <<'PY'
from pathlib import Path

from core.knowledge_catalog.qualified_search import (
    search_qualified_catalog,
    get_last_qualification_trace,
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)


def run(query, limit=8):

    rows = list(
        search_qualified_catalog(
            query,
            db_path=DB,
            limit=limit,
        )
    )

    trace = (
        get_last_qualification_trace()
        or {}
    )

    print()
    print("=" * 78)
    print("QUERY:", repr(query))
    print("=" * 78)

    print(
        "normalized :",
        repr(
            trace.get(
                "query_normalized"
            )
        ),
    )

    print(
        "changed    :",
        trace.get(
            "query_normalization_applied"
        ),
    )

    print(
        "raw original:",
        trace.get(
            "raw_original_count"
        ),
    )

    print(
        "raw normalized:",
        trace.get(
            "raw_normalized_count"
        ),
    )

    print(
        "raw merged :",
        trace.get(
            "raw_merged_count"
        ),
    )

    print(
        "qualified  :",
        len(rows),
    )

    print(
        "rescued    :",
        trace.get(
            "rescued_count",
            0,
        ),
    )

    for i, row in enumerate(
        rows[:5],
        1,
    ):
        print()
        print(f"RESULT {i}")

        print(
            " title     :",
            row.get("title")
            or row.get("subject"),
        )

        print(
            " path      :",
            row.get("file_path")
            or row.get("source_path"),
        )

        print(
            " decision  :",
            row.get(
                "qualification_decision"
            ),
        )

        print(
            " rescue    :",
            row.get(
                "qualification_rescue",
                False,
            ),
        )

        print(
            " reason    :",
            row.get(
                "qualification_rescue_reason"
            ),
        )

        print(
            " excerpt   :",
            str(
                row.get("excerpt")
                or row.get("chunk_text")
                or ""
            )[:500].replace(
                "\n",
                " ",
            ),
        )

    return rows, trace


tests = {}

QUERIES = (
    "urban warfare",

    '"urban warfare"',

    "Do you have any information on urban warfare?",

    "Tell me about urban warfare.",

    "What do you know about urban warfare?",

    "urban terrain",

    "What is C++?",

    "What does RFC 9110 define?",

    "zzqv nonexistent hyperbanana doctrine 94731",
)

for query in QUERIES:
    tests[query] = run(query)


failures = []


# ------------------------------------------------------------------
# Positive controls
# ------------------------------------------------------------------

for query in (
    "urban warfare",
    '"urban warfare"',
    "Do you have any information on urban warfare?",
    "Tell me about urban warfare.",
    "What do you know about urban warfare?",
    "urban terrain",
    "What is C++?",
):
    rows, _ = tests[query]

    if not rows:
        failures.append(
            "positive control returned zero results: "
            + repr(query)
        )


# ------------------------------------------------------------------
# Normalization behavior
# ------------------------------------------------------------------

_, natural_trace = tests[
    "Do you have any information on urban warfare?"
]

if natural_trace.get(
    "query_normalized"
) != "urban warfare":
    failures.append(
        "natural-language urban-warfare query "
        "did not normalize to 'urban warfare'"
    )

if not natural_trace.get(
    "query_normalization_applied"
):
    failures.append(
        "normalization trace did not record "
        "the transformation"
    )


# ------------------------------------------------------------------
# Exact content evidence
# ------------------------------------------------------------------

natural_rows, _ = tests[
    "Do you have any information on urban warfare?"
]

natural_evidence = " ".join(
    str(
        row.get("excerpt")
        or row.get("chunk_text")
        or ""
    ).lower()
    for row in natural_rows
)

if "urban warfare" not in natural_evidence:
    failures.append(
        "natural-language urban-warfare results "
        "do not contain exact content evidence"
    )


# ------------------------------------------------------------------
# C++ precision regression
# ------------------------------------------------------------------

cpp_rows, _ = tests[
    "What is C++?"
]

if not cpp_rows:
    failures.append(
        "C++ positive control regressed"
    )

else:
    top = cpp_rows[0]

    top_text = " ".join(
        (
            str(
                top.get("title")
                or ""
            ),
            str(
                top.get("subject")
                or ""
            ),
            str(
                top.get("excerpt")
                or ""
            ),
        )
    ).lower()

    if "c++" not in top_text:
        failures.append(
            "C++ top result no longer contains C++"
        )


# ------------------------------------------------------------------
# Negative control
# ------------------------------------------------------------------

negative_rows, _ = tests[
    "zzqv nonexistent hyperbanana doctrine 94731"
]

if negative_rows:
    failures.append(
        "negative gibberish control returned "
        f"{len(negative_rows)} result(s)"
    )


# ------------------------------------------------------------------
# RFC 9110 remains diagnostic, not mandatory.
#
# We already established that this corpus may not currently be
# materialized. R1.1 must not fake success for it.
# ------------------------------------------------------------------

rfc_rows, _ = tests[
    "What does RFC 9110 define?"
]

print()
print(
    "RFC 9110 diagnostic:",
    len(rfc_rows),
    "qualified result(s)",
)


if failures:

    print()
    print("=" * 78)
    print("FAIL: R1.1 REGRESSION CERTIFICATION")
    print("=" * 78)

    for failure in failures:
        print(" -", failure)

    raise SystemExit(1)


print()
print("=" * 78)
print("PASS: R1.1 RETRIEVAL CERTIFICATION")
print("=" * 78)

print(
    "Natural conversational queries now reach "
    "the canonical topic retrieval path."
)

print(
    "Existing canonical queries remain functional."
)

print(
    "Negative gibberish control remains empty."
)
PY


# ======================================================================
# EXECUTIVE GROUNDING CERTIFICATION
# ======================================================================

echo
echo "======================================================================"
echo " EXECUTIVE GROUNDING CERTIFICATION"
echo "======================================================================"

"$PYTHON" - <<'PY'
from core.src.routes.api import (
    conversation_service,
)

svc = conversation_service
grounder = svc.orchestrator.grounding_service

QUESTIONS = (
    "Do you have any information on urban warfare?",
    "Tell me about urban warfare.",
    "What is C++?",
)

failures = []

for question in QUESTIONS:

    print()
    print("=" * 76)
    print("QUESTION:", question)
    print("=" * 76)

    objectives = svc.compiler.compile(
        question
    )

    print("objectives:")

    for objective in objectives:
        print(
            " -",
            objective.text,
        )

    # We deliberately use the live grounding service's internal
    # objective path here. This avoids inventing an
    # ExecutiveRequestContext constructor contract and tests the exact
    # method that ground(context) delegates to.
    evidence = []
    gaps = []

    for objective in objectives:

        result = grounder._ground_objective(
            objective
        )

        # Handle the currently observed tuple contract conservatively.
        if (
            isinstance(result, tuple)
            and len(result) == 2
        ):
            objective_evidence, gap = result

            evidence.extend(
                list(
                    objective_evidence
                    or ()
                )
            )

            if gap is not None:
                gaps.append(gap)

        else:
            raise SystemExit(
                "FAIL: unexpected _ground_objective "
                f"return contract: {result!r}"
            )

    print(
        "evidence:",
        len(evidence),
    )

    print(
        "gaps    :",
        len(gaps),
    )

    for item in evidence[:5]:
        print()
        print(
            " subject:",
            item.subject,
        )

        print(
            " path   :",
            item.source_path,
        )

        print(
            " conf   :",
            item.confidence,
        )

        print(
            " text   :",
            item.excerpt[:500].replace(
                "\n",
                " ",
            ),
        )

    if not evidence:
        failures.append(
            f"Executive grounding returned zero "
            f"evidence for {question!r}"
        )


if failures:

    print()
    print("=" * 76)
    print("FAIL: EXECUTIVE GROUNDING")
    print("=" * 76)

    for failure in failures:
        print(" -", failure)

    raise SystemExit(1)


print()
print("=" * 76)
print("PASS: EXECUTIVE GROUNDING")
print("=" * 76)
PY


echo
echo "======================================================================"
echo " INSTALLED"
echo " GENESIS KNOWLEDGE RETRIEVAL R1.1"
echo " CONVERSATIONAL QUERY NORMALIZATION"
echo "======================================================================"

echo
echo "Changed:"
echo "  core/knowledge_catalog/qualified_search.py"

echo
echo "Preserved:"
echo "  Qualification Gate Repair R1"
echo "  QualificationEngine thresholds"
echo "  catalog.sqlite"
echo "  runtime FTS"
echo "  grounding.py"
echo "  orchestrator.py"
echo "  synthesis/model routing"
echo "  UI Revision 3.3"

echo
echo "New behavior:"
echo "  natural question -> conservative topical query"
echo "  original query   -> still searched"
echo "  normalized query -> searched when different"
echo "  candidate pools  -> merged and deduplicated"
echo "  qualification    -> evaluates topical query"
echo "  trace            -> records normalization provenance"

echo
echo "Backup:"
echo "  $BACKUP"

echo
echo "======================================================================"
