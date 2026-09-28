#!/usr/bin/env bash

set -Eeuo pipefail


REPO_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
    pwd
)"

cd "$REPO_ROOT"


PYTHON_BIN="${PYTHON_BIN:-python}"

KNOWLEDGE_DB="${JARVIS_KNOWLEDGE_DB:-\
/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite}"


print_header() {

    echo
    echo "======================================================================"
    echo "$1"
    echo "======================================================================"
}


print_step() {

    echo
    echo "$1"
    echo "----------------------------------------------------------------------"
}


print_header "PHASE V-B.5 — RETRIEVAL INTELLIGENCE VERIFICATION"

echo "Repository : $REPO_ROOT"
echo "Python     : $($PYTHON_BIN --version 2>&1)"
echo "Database   : $KNOWLEDGE_DB"


print_step "1. Repository state"

git status --short

echo

git branch --show-current

echo

git log --oneline --decorate -5


print_step "2. Compile Retrieval Intelligence"

"$PYTHON_BIN" -m py_compile \
    knowledge_engine/retrieval_intelligence/__init__.py \
    knowledge_engine/retrieval_intelligence/models.py \
    knowledge_engine/retrieval_intelligence/normalization.py \
    knowledge_engine/retrieval_intelligence/providers.py \
    knowledge_engine/retrieval_intelligence/merger.py \
    knowledge_engine/retrieval_intelligence/filtering.py \
    knowledge_engine/retrieval_intelligence/director.py \
    knowledge_engine/search/service.py \
    knowledge_engine/tests/test_ranking.py \
    knowledge_engine/tests/test_ranked_search_service.py \
    knowledge_engine/tests/test_retrieval_intelligence.py

echo "Compilation passed."


print_step "3. Verify imports"

"$PYTHON_BIN" - <<'PY'
from knowledge_engine.retrieval_intelligence import (
    CandidateFilter,
    CandidateMerger,
    RetrievalCandidate,
    RetrievalDiagnostics,
    RetrievalDirector,
    StaticRetrievalProvider,
    VectorRetrievalProvider,
)
from knowledge_engine.search.service import SearchService
from knowledge_engine.services.ranking import RankingService

assert CandidateFilter is not None
assert CandidateMerger is not None
assert RetrievalCandidate is not None
assert RetrievalDiagnostics is not None
assert RetrievalDirector is not None
assert StaticRetrievalProvider is not None
assert VectorRetrievalProvider is not None
assert SearchService is not None
assert RankingService is not None

print("Retrieval Intelligence imports passed.")
PY


print_step "4. Run ranking-engine regression tests"

"$PYTHON_BIN" -m unittest \
    knowledge_engine.tests.test_ranking \
    -v


print_step "5. Run ranked-search regression tests"

"$PYTHON_BIN" -m unittest \
    knowledge_engine.tests.test_ranked_search_service \
    -v


print_step "6. Run Retrieval Intelligence tests"

"$PYTHON_BIN" -m unittest \
    knowledge_engine.tests.test_retrieval_intelligence \
    -v


print_step "7. Run complete Phase V regression suite"

"$PYTHON_BIN" -m unittest \
    knowledge_engine.tests.test_ranking \
    knowledge_engine.tests.test_ranked_search_service \
    knowledge_engine.tests.test_retrieval_intelligence \
    -v


print_step "8. Verify weak-result filtering"

"$PYTHON_BIN" - <<'PY'
from knowledge_engine.retrieval_intelligence import (
    RetrievalDirector,
    StaticRetrievalProvider,
)


provider = StaticRetrievalProvider(
    name="vector",
    candidates=[
        (
            -0.06,
            "/docs/unrelated.pdf",
            0,
            "Unrelated content with no SQLite information.",
        ),
        (
            0.83,
            "/docs/sqlite-reference.pdf",
            1,
            (
                "SQLite indexes improve query performance by reducing "
                "unnecessary table scans."
            ),
        ),
    ],
)

director = RetrievalDirector(
    providers=[provider],
    minimum_similarity=0.55,
)

results = director.search(
    "SQLite indexes",
    limit=5,
)

assert len(results) == 1, (
    f"Expected exactly one accepted result; received {len(results)}."
)

assert results[0]["source"] == "/docs/sqlite-reference.pdf"

diagnostics = director.last_diagnostics

assert diagnostics is not None
assert diagnostics.retrieved_candidates == 2
assert diagnostics.accepted_candidates == 1
assert diagnostics.rejected_candidates == 1

print("Weak-result filtering passed.")
print(
    "Diagnostics:",
    diagnostics.as_dict(),
)
PY


print_step "9. Verify production database exists"

if [[ ! -f "$KNOWLEDGE_DB" ]]; then

    echo "ERROR: Knowledge database not found:"
    echo "       $KNOWLEDGE_DB"

    exit 1

fi

echo "Knowledge database found."


print_step "10. Run production retrieval diagnostics"

JARVIS_KNOWLEDGE_DB="$KNOWLEDGE_DB" \
"$PYTHON_BIN" - <<'PY'
import os

from pathlib import Path
from pprint import pprint

from knowledge_engine.retrieval_intelligence import RetrievalDirector
from knowledge_engine.storage.database import KnowledgeDatabase


database_path = Path(
    os.environ["JARVIS_KNOWLEDGE_DB"]
)

database = KnowledgeDatabase(database_path)

director = RetrievalDirector(database)

query = "SQLite embeddings retrieval"

results = director.search(
    query=query,
    limit=20,
)

print()
print(f"Query               : {query}")
print(f"Accepted candidates : {len(results)}")
print()

diagnostics = director.last_diagnostics

if diagnostics is None:

    raise AssertionError(
        "Retrieval Director did not produce diagnostics."
    )

pprint(diagnostics.as_dict())

assert (
    diagnostics.retrieved_candidates
    >= diagnostics.accepted_candidates
)

assert (
    diagnostics.merged_candidates
    >= diagnostics.accepted_candidates
)

assert (
    diagnostics.rejected_candidates
    >= 0
)

print()
print("Production retrieval diagnostics passed.")
PY


print_step "11. Run known-content retrieval diagnostic"

JARVIS_KNOWLEDGE_DB="$KNOWLEDGE_DB" \
"$PYTHON_BIN" - <<'PY'
import os

from pathlib import Path
from pprint import pprint

from knowledge_engine.retrieval_intelligence import RetrievalDirector
from knowledge_engine.storage.database import KnowledgeDatabase


database = KnowledgeDatabase(
    Path(
        os.environ["JARVIS_KNOWLEDGE_DB"]
    )
)

director = RetrievalDirector(database)

query = "Ahmed Deedat South Africa"

results = director.search(
    query=query,
    limit=10,
)

diagnostics = director.last_diagnostics

if diagnostics is None:

    raise AssertionError(
        "Known-content search produced no diagnostics."
    )

print()
print(f"Query               : {query}")
print(f"Accepted candidates : {len(results)}")
print()

pprint(diagnostics.as_dict())

for index, result in enumerate(
    results[:3],
    start=1,
):

    print()
    print(
        f"{index}. "
        f"{result.get('source', '<unknown>')}"
    )

    print(
        "   Similarity : "
        f"{float(result.get('retrieval_score_normalized', 0.0)):.6f}"
    )

    print(
        "   Provider   : "
        f"{result.get('retrieval_provider', '<unknown>')}"
    )

    print()

    print(
        str(result.get("text", ""))[:300]
    )

print()
print("Known-content diagnostic completed.")
PY


print_step "12. Run Phase IV-B regression"

./dev/verify_phase_4b.sh


print_step "13. Run JARVIS Doctor"

"$PYTHON_BIN" -m dev.doctor.doctor


print_header "PHASE V-B.5 VERIFICATION COMPLETE"

echo "Retrieval Intelligence package : PASS"
echo "Ranking regression             : PASS"
echo "Ranked-search regression        : PASS"
echo "Retrieval filtering             : PASS"
echo "Retrieval diagnostics           : PASS"
echo "Phase IV-B regression           : PASS"
echo "JARVIS Doctor                   : PASS"
echo
