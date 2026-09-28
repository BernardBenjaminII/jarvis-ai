#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$PROJECT_ROOT"
PYTHON_BIN="${PYTHON_BIN:-python}"
PASSED=0
FAILED=0
LOG_FILE="$(mktemp)"
trap 'rm -f "$LOG_FILE"' EXIT

run_check() {
    local label="$1"
    shift
    if "$@" >"$LOG_FILE" 2>&1; then
        echo "[PASS] $label"
        PASSED=$((PASSED + 1))
    else
        echo "[FAIL] $label"
        cat "$LOG_FILE"
        FAILED=$((FAILED + 1))
    fi
}

echo
echo "======================================================================"
echo "JARVIS GEN 2 — PHASE X-C1 COGNITIVE REPRESENTATION FOUNDATION"
echo "======================================================================"

run_check "Phase X-B prerequisite" test -x dev/verify_phase_xb.sh
run_check "Representation compilation" "$PYTHON_BIN" -m compileall -q core/representation
run_check "Structural boundaries" "$PYTHON_BIN" dev/verification/verify_phase_xc1_cognitive_representation.py
run_check "Unit tests" "$PYTHON_BIN" -m unittest tests.test_phase_xc1_cognitive_representation
run_check "Stable public imports" "$PYTHON_BIN" -c "from core.representation import ArtifactKind, ArtifactReference, DeterministicSemanticSegmenter, SegmentKind, SegmentationRequest, SegmentationResult, SemanticSegment, SourceSpan, segment_text"
run_check "Deterministic smoke test" "$PYTHON_BIN" -c "from core.representation import segment_text; t='Assessment\n\nOne responded. Two failed.'; a=segment_text(artifact_id='smoke', text=t); b=segment_text(artifact_id='smoke', text=t); assert a == b; assert a.segment_count == 3"

echo "----------------------------------------------------------------------"
printf "Checks passed : %s\n" "$PASSED"
printf "Checks failed : %s\n" "$FAILED"

if (( FAILED == 0 )); then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "======================================================================"
exit 1
