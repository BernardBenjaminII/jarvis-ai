#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A1"
echo "REASONING CONTRACT AUDIT"
echo "======================================================================"
echo

failures=0

pass() {
    echo "[PASS] $1"
}

fail() {
    echo "[FAIL] $1"
    failures=$((failures + 1))
}

check_file() {
    local path="$1"

    if [ -f "$path" ]; then
        pass "$path"
    else
        fail "$path"
    fi
}

check_file "core/reasoning/models.py"
check_file "dev/tools/audit_reasoning_contracts.py"
check_file "dev/verify_genesis_1a1.sh"

if "$PYTHON_BIN" -m py_compile \
    core/reasoning/models.py \
    dev/tools/audit_reasoning_contracts.py
then
    pass "Reasoning contracts and audit tool compile"
else
    fail "Reasoning contracts and audit tool compile"
fi

if "$PYTHON_BIN" dev/tools/audit_reasoning_contracts.py; then
    pass "Reasoning contract audit generated"
else
    fail "Reasoning contract audit generated"
fi

check_file \
    "docs/architecture/convergence/genesis_1a1_reasoning_contract_audit.json"
check_file \
    "docs/architecture/convergence/genesis_1a1_reasoning_contract_audit.md"

if "$PYTHON_BIN" dev/tools/audit_reasoning_contracts.py --check; then
    pass "Generated audit reports are deterministic and current"
else
    fail "Generated audit reports are deterministic and current"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    HypothesisAssessment,
    PlanningRecommendation,
    ReasoningRequest,
    ReasoningResult,
    ReasoningTraceStep,
    canonical_fingerprint,
    canonicalize,
)

report_path = Path(
    "docs/architecture/convergence/"
    "genesis_1a1_reasoning_contract_audit.json"
)
report = json.loads(report_path.read_text(encoding="utf-8"))

expected_contracts = {
    "EvidenceItem",
    "Hypothesis",
    "ReasoningRequest",
    "HypothesisAssessment",
    "ReasoningTraceStep",
    "PlanningRecommendation",
    "ReasoningResult",
}

actual_contracts = {
    contract["name"]
    for contract in report["contracts"]
}

assert actual_contracts == expected_contracts
assert report["contract_count"] == 7
assert report["missing_expected_contracts"] == []
assert report["missing_expected_helpers"] == []

for contract in report["contracts"]:
    assert contract["frozen"] is True
    assert contract["slots"] is True
    assert contract["has_to_dict"] is True

assert report["conclusions"]["canonical_serialization_present"] is True
assert report["conclusions"]["evidence_weight_present"] is True
assert report["conclusions"]["request_fingerprint_present"] is True
assert report["conclusions"]["planning_bridge_present"] is True

assert callable(canonicalize)
assert callable(canonical_fingerprint)

assert EvidenceItem is not None
assert Hypothesis is not None
assert ReasoningRequest is not None
assert HypothesisAssessment is not None
assert ReasoningTraceStep is not None
assert PlanningRecommendation is not None
assert ReasoningResult is not None

print("[PASS] Canonical reasoning-contract assertions")
PY
then
    pass "Canonical contract structure"
else
    fail "Canonical contract structure"
fi

if "$PYTHON_BIN" - <<'PY'
from core.reasoning.enums import EvidenceKind, EvidenceStance
from core.reasoning.models import (
    EvidenceItem,
    Hypothesis,
    ReasoningRequest,
)

evidence = EvidenceItem(
    evidence_id="evidence-001",
    proposition="The observed condition is present.",
    stance=EvidenceStance.SUPPORTS,
    source_ref="verification-fixture",
    kind=EvidenceKind.FACT,
    reliability=0.8,
    confidence=0.75,
)

from math import isclose

expected_weight = evidence.reliability * evidence.confidence

assert isclose(
    evidence.weight,
    expected_weight,
    rel_tol=1e-12,
    abs_tol=1e-12,
)

hypothesis = Hypothesis(
    hypothesis_id="hypothesis-001",
    statement="The observed condition explains the target outcome.",
    supporting_evidence_ids=(evidence.evidence_id,),
)

request = ReasoningRequest(
    request_id="request-001",
    goal="Assess the target explanation.",
    evidence=(evidence,),
    hypotheses=(hypothesis,),
)

first_fingerprint = request.fingerprint
second_fingerprint = request.fingerprint

assert len(first_fingerprint) == 64
assert first_fingerprint == second_fingerprint
assert request.to_dict()["request_id"] == "request-001"

print("[PASS] Immutable reasoning-contract smoke test")
PY
then
    pass "Reasoning-contract smoke test"
else
    fail "Reasoning-contract smoke test"
fi

echo
echo "----------------------------------------------------------------------"
echo "Checks failed : ${failures}"

if [ "$failures" -eq 0 ]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: ATTENTION REQUIRED"
echo "======================================================================"
exit 1
