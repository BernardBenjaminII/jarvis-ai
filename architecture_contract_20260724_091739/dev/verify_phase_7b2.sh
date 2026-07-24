#!/usr/bin/env bash
set -uo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"
FAILED=0
LOG_FILE="/tmp/jarvis_phase_7b2_check.log"

pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s\n' "$1"; FAILED=$((FAILED + 1)); }

run_check() {
    local description="$1"
    shift
    : > "$LOG_FILE"
    if "$@" >"$LOG_FILE" 2>&1; then
        pass "$description"
    else
        fail "$description"
        sed -n '1,260p' "$LOG_FILE"
    fi
}

echo "======================================================================"
echo "JARVIS GEN 2 — PHASE VII-B2 PERSISTENT SOURCE REGISTRY"
echo "======================================================================"

run_check     "Phase VII-B2 package compilation"     "$PYTHON_BIN" -m compileall -q     knowledge_engine/source_registry     tests/test_phase_7b2_source_registry.py

run_check     "Stable source-registry public imports"     "$PYTHON_BIN" - <<'PY'
from knowledge_engine.source_registry import (
    InvalidLifecycleTransitionError,
    RegisteredSource,
    RegistrationResult,
    RegistryStats,
    SQLiteSourceRegistryRepository,
    SourceLifecycleState,
    SourceNotAdmittedError,
    SourceRegistryConflictError,
    SourceRegistryError,
    SourceRegistryNotFoundError,
    SourceRegistryService,
)
print("imports verified")
PY

run_check     "Source-registry unit tests"     "$PYTHON_BIN" -m unittest -v     tests.test_phase_7b2_source_registry

run_check     "VII-B2 depends forward on VII-B1 only"     "$PYTHON_BIN" - <<'PY'
from pathlib import Path

registry_root = Path("knowledge_engine/source_registry")
violations = []

for path in registry_root.rglob("*.py"):
    text = path.read_text(encoding="utf-8")
    if "knowledge_engine.acquisition." in text:
        violations.append(str(path))

if violations:
    raise SystemExit(
        "Source registry directly imports frozen acquisition package:\n"
        + "\n".join(violations)
    )
PY

run_check     "Persistent registry smoke test"     "$PYTHON_BIN" - <<'PY'
import tempfile
from pathlib import Path

from knowledge_engine.acquisition_control import (
    SourceAdmissionService,
    SourceKind,
    SourceProposal,
    SourceTrustTier,
)
from knowledge_engine.source_registry import (
    SourceLifecycleState,
    SourceRegistryService,
)

with tempfile.TemporaryDirectory() as tempdir:
    registry = SourceRegistryService(
        Path(tempdir) / "registry.sqlite"
    )
    decision = SourceAdmissionService().evaluate(
        SourceProposal(
            source_id="nasa",
            display_name="NASA",
            location="https://www.nasa.gov",
            kind=SourceKind.HTTPS,
            trust_tier=SourceTrustTier.OFFICIAL,
        )
    )
    first = registry.register_admission(decision)
    second = registry.register_admission(decision)

    assert first.created is True
    assert second.created is False
    assert first.source.registry_id == second.source.registry_id

    active = registry.transition(
        first.source.registry_id,
        SourceLifecycleState.ACTIVE,
    )
    assert active.lifecycle_state is SourceLifecycleState.ACTIVE
PY

if [[ -x ./dev/verify_phase_7b1.sh ]]; then
    run_check         "Phase VII-B1 source-admission regression"         env PYTHON_BIN="$PYTHON_BIN" ./dev/verify_phase_7b1.sh
else
    fail "Phase VII-B1 verification script is present and executable"
fi

echo "----------------------------------------------------------------------"
echo "Checks failed : $FAILED"

if [[ "$FAILED" -eq 0 ]]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "======================================================================"
exit 1
