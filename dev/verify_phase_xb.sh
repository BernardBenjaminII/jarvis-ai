#!/usr/bin/env bash
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
LOG="/tmp/jarvis_phase_xb.log"
PASSED=0
FAILED=0
cd "$ROOT"

run_check() {
    local description="$1"
    shift
    if "$@" >"$LOG" 2>&1; then
        printf '[PASS] %s\n' "$description"
        PASSED=$((PASSED + 1))
    else
        printf '[FAIL] %s\n' "$description"
        cat "$LOG"
        FAILED=$((FAILED + 1))
    fi
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE X-B HYPOTHESIS + KNOWLEDGE INTEGRATION"
echo "======================================================================"

run_check "Phase X prerequisite"     "$PYTHON_BIN" -c 'from core.reasoning import ReasoningEngine; assert ReasoningEngine'
run_check "Reasoning integration compilation"     "$PYTHON_BIN" -m compileall -q core/reasoning
run_check "Phase X-B structural boundaries"     "$PYTHON_BIN" dev/verification/verify_phase_xb_hypothesis_knowledge.py
run_check "Phase X-B unit tests"     "$PYTHON_BIN" -m unittest -v tests.test_phase_xb_hypothesis_knowledge
run_check "Phase X regression tests"     "$PYTHON_BIN" -m unittest -v tests.test_phase_x_reasoning_foundation
run_check "Stable public integration imports"     "$PYTHON_BIN" -c 'from core.reasoning import KnowledgeEvidenceAdapter, DeterministicHypothesisGenerator, KnowledgeReasoningPipeline'
run_check "Deterministic knowledge reasoning smoke test"     "$PYTHON_BIN" -c '
from core.reasoning import KnowledgeReasoningPipeline
results = ({
    "source": "/docs/a.pdf",
    "chunk_index": 1,
    "text": "Structured evidence supports auditable reasoning.",
    "ranking_score": 0.91,
    "quality": 96,
},)
pipeline = KnowledgeReasoningPipeline(lambda query, limit: results)
first = pipeline.reason(goal="Integrate knowledge with reasoning")
second = pipeline.reason(goal="Integrate knowledge with reasoning")
assert first.reasoning.selected_hypothesis_id is not None
assert first.reasoning.fingerprint == second.reasoning.fingerprint
'

echo "----------------------------------------------------------------------"
printf 'Checks passed : %d\n' "$PASSED"
printf 'Checks failed : %d\n' "$FAILED"
if [ "$FAILED" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi
echo "Overall status: FAILED"
echo "======================================================================"
exit 1
