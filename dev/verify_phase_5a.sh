#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
    pwd
)"

cd "$REPO_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo
echo "== Phase V-A: Knowledge Ranking Engine =="
echo

echo "Repository: $REPO_ROOT"
echo "Python    : $("$PYTHON_BIN" --version 2>&1)"
echo

echo "1. Compiling ranking package..."
"$PYTHON_BIN" -m compileall -q \
    knowledge_engine/ranking \
    knowledge_engine/services/ranking.py \
    knowledge_engine/tests/test_ranking.py

echo "   Compilation passed."
echo

echo "2. Verifying imports..."
"$PYTHON_BIN" - <<'PY'
from knowledge_engine.ranking import (
    KnowledgeRanker,
    RankingBreakdown,
    RankingCandidate,
    RankingWeights,
    rank_results,
)
from knowledge_engine.services.ranking import (
    RankingService,
    rank_search_results,
)

print("   Ranking imports passed.")
PY

echo
echo "3. Running ranking unit tests..."
"$PYTHON_BIN" -m unittest \
    knowledge_engine.tests.test_ranking \
    -v

echo
echo "4. Running synthetic ranking demonstration..."
"$PYTHON_BIN" - <<'PY'
from knowledge_engine.services.ranking import rank_search_results

query = "SQLite database transactions"

results = [
    {
        "text": (
            "Ahmed Deedat was born in the district of Surat, India, "
            "in 1918."
        ),
        "source": "/ebooks/deen/ahmed-deedat.pdf",
        "chunk_index": 0,
        "score": 0.0428,
        "quality": 100,
    },
    {
        "text": (
            "SQLite transactions are atomic. Write-ahead logging allows "
            "readers and writers to operate concurrently while preserving "
            "database recoverability."
        ),
        "source": "/docs/reference/sqlite-manual.pdf",
        "chunk_index": 14,
        "score": 0.81,
        "quality": 96,
    },
    {
        "text": "Use UltraISO to extract MP3 files to your computer.",
        "source": "/downloads/read-me.txt",
        "chunk_index": 0,
        "score": 0.0375,
        "quality": 100,
    },
    {
        "text": (
            "A database transaction groups operations into a single "
            "atomic unit of work."
        ),
        "source": "/docs/database-systems.pdf",
        "chunk_index": 31,
        "score": 0.72,
        "quality": 91,
    },
]

ranked = rank_search_results(query, results, limit=3)

print()
print("=" * 72)
print("RANKED RESULTS")
print("=" * 72)

for index, result in enumerate(ranked, start=1):
    ranking = result["ranking"]

    print(f"{index}. {result['source']}")
    print(f"   Ranking score : {result['ranking_score']:.4f}")
    print(f"   Semantic      : {ranking['semantic']:.4f}")
    print(f"   Lexical       : {ranking['lexical']:.4f}")
    print(f"   Authority     : {ranking['authority']:.4f}")
    print(f"   Quality       : {ranking['quality']:.4f}")
    print(f"   Duplicate pen.: {ranking['duplicate_penalty']:.4f}")
    print()

assert ranked[0]["source"] == "/docs/reference/sqlite-manual.pdf"
assert all("ranking" in result for result in ranked)
assert all("ranking_score" in result for result in ranked)

print("Synthetic ranking assertions passed.")
PY

echo
echo "5. Running Phase IV regression checks..."
./dev/verify_phase_4b.sh
./dev/verify_phase_4d4.sh

echo
echo "6. Running JARVIS Doctor regression..."
"$PYTHON_BIN" -m dev.doctor.doctor

echo
echo "Phase V-A ranking foundation verification complete."
