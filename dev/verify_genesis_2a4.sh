#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

PASS_COUNT=0
FAIL_COUNT=0

print_header() {
    printf '\n'
    printf '%s\n' \
        "======================================================================"
    printf '%s\n' \
        "JARVIS GENESIS II-A4 — IMMUTABLE EVIDENCE CONTRACTS"
    printf '%s\n' \
        "======================================================================"
}

pass_check() {
    PASS_COUNT=$((PASS_COUNT + 1))
    printf '[PASS] %s\n' "$1"
}

fail_check() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    printf '[FAIL] %s\n' "$1"
}

run_check() {
    local label="$1"
    shift

    if "$@" >/dev/null 2>&1; then
        pass_check "$label"
    else
        fail_check "$label"
    fi
}

print_header

run_check \
    "Canonical Evidence package structure" \
    test -f core/reasoning/evidence/__init__.py

run_check \
    "Evidence domain exceptions" \
    test -f core/reasoning/evidence/errors.py

run_check \
    "Canonical Evidence vocabularies" \
    test -f core/reasoning/evidence/enums.py

run_check \
    "Deterministic Evidence identifiers" \
    test -f core/reasoning/evidence/identifiers.py

run_check \
    "Immutable Evidence contracts" \
    test -f core/reasoning/evidence/contracts.py

run_check \
    "Deterministic canonical serialization" \
    test -f core/reasoning/evidence/serialization.py

run_check \
    "Evidence structural validation" \
    test -f core/reasoning/evidence/validation.py

run_check \
    "Genesis II-A4 architecture document" \
    test -f \
        docs/architecture/genesis/reasoning/GENESIS_II_A4_CANONICAL_EVIDENCE_MODEL.md

run_check \
    "ADR-0019 canonical Evidence decision" \
    test -f docs/decisions/ADR-0019-canonical-evidence-model.md

if "$PYTHON_BIN" -m compileall -q core/reasoning/evidence; then
    pass_check "Evidence package compilation"
else
    fail_check "Evidence package compilation"
fi

if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
from core.reasoning.evidence import (
    AssessmentMethod,
    EvidenceAssessment,
    EvidenceContent,
    EvidenceId,
    EvidenceModality,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceRelationship,
    EvidenceRelationshipType,
    EvidenceSourceType,
    EvidenceStatusEvent,
    EvidenceTemporalScope,
    EvidenceUncertainty,
    UncertaintyKind,
    canonical_json,
)
PY
then
    pass_check "Stable public Evidence imports"
else
    fail_check "Stable public Evidence imports"
fi

if "$PYTHON_BIN" -m pytest -q \
    tests/test_genesis_2a4_evidence_contracts.py; then
    pass_check "Genesis II-A4 constitutional unit tests"
else
    fail_check "Genesis II-A4 constitutional unit tests"
fi

if "$PYTHON_BIN" - <<'PY' >/dev/null 2>&1
from datetime import datetime, timezone
from decimal import Decimal

from core.reasoning.evidence import (
    EvidenceContent,
    EvidenceModality,
    EvidenceOrigin,
    EvidenceProvenance,
    EvidenceProvenanceStep,
    EvidenceRecord,
    EvidenceSourceType,
    EvidenceTemporalScope,
    EvidenceUncertainty,
    UncertaintyKind,
    canonical_json,
)

fixed_time = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)

def build():
    return EvidenceRecord.create(
        content=EvidenceContent(
            statement="Deterministic Evidence identity smoke test.",
        ),
        origin=EvidenceOrigin(
            source_type=EvidenceSourceType.TOOL,
            source_id="genesis-ii-a4-verifier",
        ),
        provenance=EvidenceProvenance(
            steps=(
                EvidenceProvenanceStep(
                    sequence=0,
                    actor="verify_genesis_2a4",
                    mechanism="smoke-test",
                ),
            )
        ),
        temporal_scope=EvidenceTemporalScope(
            recorded_at=fixed_time,
        ),
        uncertainty=EvidenceUncertainty(
            kind=UncertaintyKind.PROBABILITY,
            probability=Decimal("1"),
        ),
        modality=EvidenceModality.OBSERVATIONAL,
    )

first = build()
second = build()

assert first.evidence_id == second.evidence_id
assert canonical_json(first) == canonical_json(second)
PY
then
    pass_check "Deterministic Evidence identity smoke test"
else
    fail_check "Deterministic Evidence identity smoke test"
fi

if ! grep -R -nE \
    '(^|[[:space:]])(requests|urllib|socket|subprocess|sqlite3|sqlalchemy)([[:space:].]|$)' \
    core/reasoning/evidence \
    --include='*.py' \
    >/dev/null 2>&1
then
    pass_check "No network, persistence, or process dependencies"
else
    fail_check "No network, persistence, or process dependencies"
fi

if grep -Fq \
    "Evidence is not belief." \
    docs/architecture/genesis/reasoning/GENESIS_II_A4_CANONICAL_EVIDENCE_MODEL.md
then
    pass_check "Evidence and Belief constitutional separation"
else
    fail_check "Evidence and Belief constitutional separation"
fi

printf '%s\n' \
    "----------------------------------------------------------------------"
printf 'Checks passed : %s\n' "$PASS_COUNT"
printf 'Checks failed : %s\n' "$FAIL_COUNT"

if (( FAIL_COUNT == 0 )); then
    printf 'Overall status: EXCELLENT\n'
    printf '%s\n' \
        "======================================================================"
    exit 0
fi

printf 'Overall status: FAILED\n'
printf '%s\n' \
    "======================================================================"
exit 1
