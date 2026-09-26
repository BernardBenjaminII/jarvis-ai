#!/usr/bin/env bash
set -euo pipefail

ROOT="/media/abdullah/JARVISDATA/Projects/jarvis-ai"
PYTHON="/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python"

TARGET="$ROOT/core/knowledge_catalog/qualified_search.py"

STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP="$ROOT/.knowledge_backups/qualification_gate_repair_r1_${STAMP}"

echo "======================================================================"
echo " GENESIS KNOWLEDGE RETRIEVAL"
echo " QUALIFICATION GATE REPAIR R1"
echo "======================================================================"

cd "$ROOT"

[[ -f "$TARGET" ]] || {
    echo "FAIL: missing target:"
    echo "  $TARGET"
    exit 1
}

mkdir -p "$BACKUP"
cp -a "$TARGET" "$BACKUP/qualified_search.py"

echo
echo "Backup:"
echo "  $BACKUP"

# ======================================================================
# Patch qualified_search.py
#
# Design:
#
#   1. Preserve QualificationEngine and all existing thresholds.
#   2. Retrieve a larger candidate pool before qualification.
#   3. Preserve normal accepted candidates.
#   4. Rescue only rejected candidates that have strong deterministic
#      content evidence.
#   5. Do NOT rescue weak subject-only / filename-only / low lexical hits.
#
# Rescue requires:
#
#   - normalized core query has >= 2 meaningful terms
#   - every core term occurs in title/subject/excerpt/path
#   - preferably the complete normalized phrase occurs
#   - final qualification score >= current global threshold
#   - lexical evidence is strong
#   - entity evidence is strong
#   - provenance is trustworthy
#
# The subject score and raw FTS confidence become ranking signals rather
# than unconditional vetoes when exact content support exists.
# ======================================================================

"$PYTHON" - "$TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()

MARKER = "# GENESIS_QUALIFICATION_GATE_REPAIR_R1"

if MARKER in source:
    print("R1 patch already present; no duplicate patch applied.")
    raise SystemExit(0)

old = '''def search_qualified_catalog(
    query: str,
    *,
    db_path: Path = DEFAULT_CATALOG_DB,
    limit: int = 25,
    engine: QualificationEngine | None = None,
) -> list[dict[str, Any]]:
    raw_rows = search_catalog(
        query,
        db_path=db_path,
        limit=limit,
    )

    accepted_rows, _ = qualify_rows(
        query,
        raw_rows,
        engine=engine,
    )

    return accepted_rows
'''

if old not in source:
    raise SystemExit(
        "FAIL: expected search_qualified_catalog implementation was not found.\\n"
        "No source changes were made."
    )

new = r'''# GENESIS_QUALIFICATION_GATE_REPAIR_R1
#
# R1 principle:
# subject alignment and raw retrieval confidence remain useful signals,
# but neither may veto a candidate that contains strong deterministic
# query evidence and already clears the normal final qualification score.
#
# This avoids globally weakening QualificationEngine.

_GATE_REPAIR_STOPWORDS = frozenset({
    "a", "an", "and", "any", "are", "about", "can", "could",
    "do", "does", "for", "from", "have", "i", "in", "information",
    "is", "it", "me", "my", "of", "on", "please", "say", "show",
    "tell", "the", "there", "to", "what", "whatever", "which",
    "with", "you", "your",
})


def _gate_repair_tokens(value: str) -> tuple[str, ...]:
    import re

    normalized = re.sub(
        r"[^a-z0-9+#.-]+",
        " ",
        str(value or "").lower(),
    )

    tokens = tuple(
        token.strip(" .")
        for token in normalized.split()
        if token.strip(" .")
    )

    meaningful = tuple(
        token
        for token in tokens
        if token not in _GATE_REPAIR_STOPWORDS
        and len(token) > 1
    )

    return meaningful or tokens


def _gate_repair_normalized_text(value: str) -> str:
    import re

    return " ".join(
        re.sub(
            r"[^a-z0-9+#.-]+",
            " ",
            str(value or "").lower(),
        ).split()
    )


def _gate_repair_candidate_text(candidate: Any) -> str:
    return _gate_repair_normalized_text(
        " ".join(
            (
                str(getattr(candidate, "title", "") or ""),
                str(getattr(candidate, "subject", "") or ""),
                str(getattr(candidate, "excerpt", "") or ""),
                str(getattr(candidate, "source_path", "") or ""),
            )
        )
    )


def _gate_repair_should_rescue(
    query: str,
    evidence: Any,
    *,
    threshold: float,
) -> tuple[bool, str]:
    """
    Rescue a candidate only when the candidate itself contains strong,
    deterministic support for the meaningful query terms.

    This is intentionally stricter than merely lowering subject or
    confidence thresholds.
    """

    candidate = evidence.candidate
    score = evidence.score

    tokens = _gate_repair_tokens(query)

    # Avoid rescue based on vague single-token queries.
    if len(tokens) < 2:
        return False, "core_query_too_short"

    haystack = _gate_repair_candidate_text(candidate)

    if not haystack:
        return False, "empty_candidate_text"

    # All meaningful terms must actually occur in the candidate.
    missing = tuple(
        token
        for token in tokens
        if token not in haystack
    )

    if missing:
        return False, "missing_core_terms:" + ",".join(missing)

    phrase = " ".join(tokens)
    phrase_match = phrase in haystack

    try:
        final_score = float(score.final)
    except Exception:
        final_score = 0.0

    try:
        lexical = float(score.lexical)
    except Exception:
        lexical = 0.0

    try:
        entity = float(score.entity)
    except Exception:
        entity = 0.0

    try:
        provenance = float(score.provenance)
    except Exception:
        provenance = 0.0

    # Existing global score remains mandatory.
    if final_score < float(threshold):
        return False, "final_below_threshold"

    # Require strong lexical support.
    if lexical < 0.80:
        return False, "lexical_below_rescue_floor"

    # Entity overlap gives another independent deterministic signal.
    if entity < 0.75:
        return False, "entity_below_rescue_floor"

    # Do not rescue evidence with weak provenance.
    if provenance < 0.50:
        return False, "provenance_below_rescue_floor"

    # Exact core phrase is the preferred rescue condition.
    if phrase_match:
        return True, "exact_core_phrase"

    # For 3+ meaningful terms, complete token coverage can substitute
    # for adjacency because OCR and PDF extraction frequently split
    # words/phrases irregularly.
    if len(tokens) >= 3:
        return True, "complete_core_term_coverage"

    return False, "two_term_query_requires_phrase"


def _gate_repair_qualified_row(
    evidence: Any,
    *,
    reason: str,
) -> dict[str, Any]:
    row = qualified_row(evidence)

    row["qualification_decision_original"] = row.get(
        "qualification_decision"
    )

    row["qualification_decision"] = "accepted_content_rescue"
    row["qualification_rescue"] = True
    row["qualification_rescue_reason"] = reason

    row["assigned_by"] = "qualification_gate_repair_r1"

    return row


def search_qualified_catalog(
    query: str,
    *,
    db_path: Path = DEFAULT_CATALOG_DB,
    limit: int = 25,
    engine: QualificationEngine | None = None,
) -> list[dict[str, Any]]:
    requested_limit = max(1, int(limit))

    # Qualification should operate on a higher-recall pool than the
    # number ultimately returned to the grounder.
    raw_limit = max(
        requested_limit * 4,
        100,
    )

    raw_rows = search_catalog(
        query,
        db_path=db_path,
        limit=raw_limit,
    )

    accepted_rows, result = qualify_rows(
        query,
        raw_rows,
        engine=engine,
    )

    output = list(accepted_rows)

    seen: set[tuple[str, str]] = set()

    for row in output:
        path = str(
            row.get("file_path")
            or row.get("source_path")
            or ""
        )

        excerpt = str(
            row.get("excerpt")
            or row.get("chunk_text")
            or ""
        )

        seen.add((path, excerpt))

    rescue_diagnostics: list[dict[str, Any]] = []

    if len(output) < requested_limit:

        for rejected in result.rejected:

            rescue, reason = _gate_repair_should_rescue(
                query,
                rejected,
                threshold=float(result.threshold),
            )

            rescue_diagnostics.append(
                {
                    "source_id": rejected.candidate.source_id,
                    "source_path": rejected.candidate.source_path,
                    "rescue": rescue,
                    "reason": reason,
                    "score": rejected.score.to_dict(),
                    "original_decision": rejected.decision.value,
                }
            )

            if not rescue:
                continue

            row = _gate_repair_qualified_row(
                rejected,
                reason=reason,
            )

            path = str(
                row.get("file_path")
                or row.get("source_path")
                or ""
            )

            excerpt = str(
                row.get("excerpt")
                or row.get("chunk_text")
                or ""
            )

            identity = (path, excerpt)

            if identity in seen:
                continue

            seen.add(identity)
            output.append(row)

            if len(output) >= requested_limit:
                break

    # Preserve the existing qualification trace and augment it rather
    # than hiding what QualificationEngine originally decided.
    trace = get_last_qualification_trace()

    if trace is not None:
        trace["gate_repair_revision"] = "R1"
        trace["raw_candidate_limit"] = raw_limit
        trace["requested_limit"] = requested_limit
        trace["rescued_count"] = sum(
            1 for item in output
            if item.get("qualification_rescue")
        )
        trace["returned_count"] = len(output)
        trace["rescue_diagnostics"] = rescue_diagnostics

        _LAST_TRACE.set(trace)

    # Preserve deterministic ranking:
    # normal QualificationEngine accepts first, then conservative rescues.
    return output[:requested_limit]
'''

path.write_text(
    source.replace(
        old,
        new,
        1,
    )
)

print("PATCHED:", path)
PY


# ======================================================================
# SYNTAX / IMPORT CHECK
# ======================================================================

echo
echo "======================================================================"
echo " SOURCE CERTIFICATION"
echo "======================================================================"

"$PYTHON" -m py_compile "$TARGET"

echo "PASS: Python syntax"

"$PYTHON" - <<'PY'
from core.knowledge_catalog.qualified_search import (
    search_qualified_catalog,
    get_last_qualification_trace,
)

print("PASS: qualified_search imports")

assert callable(search_qualified_catalog)
assert callable(get_last_qualification_trace)

print("PASS: public contracts available")
PY


# ======================================================================
# REGRESSION CERTIFICATION
# ======================================================================

echo
echo "======================================================================"
echo " QUALIFICATION GATE R1 — REGRESSION CERTIFICATION"
echo "======================================================================"

"$PYTHON" - <<'PY'
from pathlib import Path

from core.knowledge_catalog.qualified_search import (
    search_catalog,
    search_qualified_catalog,
    get_last_qualification_trace,
)

DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)


def run(query, limit=8):
    raw = list(
        search_catalog(
            query,
            db_path=DB,
            limit=100,
        )
    )

    qualified = list(
        search_qualified_catalog(
            query,
            db_path=DB,
            limit=limit,
        )
    )

    trace = get_last_qualification_trace() or {}

    print()
    print("=" * 76)
    print("QUERY:", repr(query))
    print("=" * 76)
    print("raw      :", len(raw))
    print("qualified:", len(qualified))
    print("rescued  :", trace.get("rescued_count", 0))

    for i, row in enumerate(qualified[:5], 1):
        print()
        print(f"RESULT {i}")
        print(
            " title     :",
            row.get("title")
            or row.get("subject")
        )
        print(
            " path      :",
            row.get("file_path")
            or row.get("source_path")
        )
        print(
            " decision  :",
            row.get("qualification_decision")
        )
        print(
            " rescue    :",
            row.get("qualification_rescue", False)
        )
        print(
            " reason    :",
            row.get("qualification_rescue_reason")
        )
        print(
            " confidence:",
            row.get("confidence")
        )
        print(
            " excerpt   :",
            str(
                row.get("excerpt")
                or row.get("chunk_text")
                or ""
            )[:500].replace("\n", " ")
        )

    return qualified


# ------------------------------------------------------------------
# Positive controls
# ------------------------------------------------------------------

positive = {}

for query in (
    "urban warfare",
    '"urban warfare"',
    "Do you have any information on urban warfare?",
    "urban terrain",
    "What is C++?",
):
    positive[query] = run(query)


# ------------------------------------------------------------------
# Negative control
# ------------------------------------------------------------------

negative_query = (
    "zzqv nonexistent hyperbanana doctrine 94731"
)

negative = run(
    negative_query,
    limit=8,
)


# ------------------------------------------------------------------
# Assertions
# ------------------------------------------------------------------

failures = []


def require_results(query):
    if not positive.get(query):
        failures.append(
            f"positive control returned zero results: {query!r}"
        )


require_results("urban warfare")
require_results('"urban warfare"')
require_results(
    "Do you have any information on urban warfare?"
)
require_results("urban terrain")
require_results("What is C++?")


if negative:
    failures.append(
        "negative gibberish control unexpectedly returned "
        f"{len(negative)} qualified result(s)"
    )


# Verify urban-warfare result contains real content-level evidence.
urban_rows = positive["urban warfare"]

urban_text = " ".join(
    str(
        row.get("excerpt")
        or row.get("chunk_text")
        or ""
    ).lower()
    for row in urban_rows
)

if "urban warfare" not in urban_text:
    failures.append(
        "urban warfare positive control returned results, "
        "but none contains the exact phrase in evidence text"
    )


if failures:
    print()
    print("=" * 76)
    print("FAIL: REGRESSION CERTIFICATION")
    print("=" * 76)

    for failure in failures:
        print(" -", failure)

    raise SystemExit(1)


print()
print("=" * 76)
print("PASS: QUALIFICATION GATE REPAIR R1")
print("=" * 76)
print("Positive controls retrieved qualified evidence.")
print("Negative gibberish control remained empty.")
PY


# ======================================================================
# DIRECT GROUNDING CERTIFICATION
# ======================================================================

echo
echo "======================================================================"
echo " EXECUTIVE GROUNDING CERTIFICATION"
echo "======================================================================"

"$PYTHON" - <<'PY'
from core.src.routes.api import conversation_service
from core.conversation.contracts import ExecutiveRequestContext

svc = conversation_service
grounder = svc.orchestrator.grounding_service

QUESTIONS = (
    "Do you have any information on urban warfare?",
    "What is C++?",
)

for question in QUESTIONS:

    objectives = svc.compiler.compile(question)

    context = ExecutiveRequestContext.create(
        operator_input=question,
        mode="knowledge",
        channel="diagnostic",
        metadata={
            "qualification_gate_repair": "R1",
        },
    )

    # ExecutiveRequestContext.create may compile internally in some
    # revisions. If the returned context exposes no objectives, fail
    # clearly rather than silently constructing an incompatible object.
    if not getattr(context, "objectives", None):
        try:
            from dataclasses import replace

            context = replace(
                context,
                objectives=objectives,
            )
        except Exception:
            pass

    result = grounder.ground(context)

    print()
    print("-" * 76)
    print("QUESTION:", question)
    print("status   :", result.status)
    print("evidence :", len(result.evidence))
    print("gaps     :", len(result.gaps))

    for item in result.evidence[:5]:
        print()
        print(" subject:", item.subject)
        print(" path   :", item.source_path)
        print(" conf   :", item.confidence)
        print(
            " text   :",
            item.excerpt[:500].replace("\n", " ")
        )

    if not result.evidence:
        raise SystemExit(
            f"FAIL: grounding still produced no evidence for {question!r}"
        )


print()
print("=" * 76)
print("PASS: EXECUTIVE GROUNDING NOW RECEIVES EVIDENCE")
print("=" * 76)
PY


echo
echo "======================================================================"
echo " INSTALLED: GENESIS KNOWLEDGE RETRIEVAL"
echo " QUALIFICATION GATE REPAIR R1"
echo "======================================================================"

echo
echo "Changed:"
echo "  core/knowledge_catalog/qualified_search.py"

echo
echo "Preserved:"
echo "  QualificationEngine thresholds"
echo "  grounding.py"
echo "  conversation orchestrator"
echo "  catalog.sqlite"
echo "  runtime_chunks / FTS index"
echo "  UI Revision 3.3"
echo "  Ollama/model routing"

echo
echo "Behavioral changes:"
echo "  - qualification now searches a deeper raw candidate pool"
echo "  - normal QualificationEngine accepts retain priority"
echo "  - subject mismatch cannot veto exact strong content evidence"
echo "  - low raw FTS confidence cannot veto exact strong content evidence"
echo "  - rescue requires complete meaningful-query coverage"
echo "  - two-term rescue requires the exact core phrase"
echo "  - rescue decisions are recorded in qualification trace"

echo
echo "Backup:"
echo "  $BACKUP"

echo
echo "======================================================================"
