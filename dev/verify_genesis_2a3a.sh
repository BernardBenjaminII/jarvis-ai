#!/usr/bin/env bash

###############################################################################
#
# JARVIS GENESIS II-A3A
#
# Verification Architecture Certification
#
###############################################################################

set -Eeuo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

PYTHON_BIN="${PYTHON_BIN:-python}"
export PYTHON_BIN

PASSED=0
FAILED=0

pass() {
    PASSED=$((PASSED + 1))
    echo "[PASS] $1"
}

fail() {
    FAILED=$((FAILED + 1))
    echo "[FAIL] $1"
}

check() {
    local description="$1"
    shift

    if "$@"; then
        pass "${description}"
    else
        fail "${description}"
    fi
}

echo
echo "======================================================================"
echo "JARVIS GENESIS II-A3A — VERIFICATION ARCHITECTURE"
echo "======================================================================"

check \
    "Shell syntax" \
    bash -n \
    dev/run_verification_manifest.sh \
    dev/verify_knowledge_all.sh \
    dev/verify_genesis_all.sh \
    dev/verify_all.sh \
    dev/verify_genesis_2a3a.sh

check \
    "Required manifests exist" \
    bash -c '
        test -f dev/verification/manifests/knowledge.manifest &&
        test -f dev/verification/manifests/genesis.manifest
    '

check \
    "Manifest paths are repository-relative and unique" \
    "$PYTHON_BIN" - <<'PY'
from pathlib import Path

for manifest in (
    Path("dev/verification/manifests/knowledge.manifest"),
    Path("dev/verification/manifests/genesis.manifest"),
):
    entries = []
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith("/"), f"absolute path in {manifest}: {line}"
        assert ".." not in line, f"path traversal in {manifest}: {line}"
        entries.append(line)

    assert entries, f"empty manifest: {manifest}"
    assert len(entries) == len(set(entries)), f"duplicate entries: {manifest}"
PY

check \
    "Every registered verifier exists and is executable" \
    "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import os

for manifest in Path("dev/verification/manifests").glob("*.manifest"):
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        path = Path(line)
        assert path.is_file(), f"missing verifier: {path}"
        assert os.access(path, os.X_OK), f"not executable: {path}"
PY

check \
    "Knowledge manifest preserves certified Phase VI–VII order" \
    "$PYTHON_BIN" - <<'PY'
from pathlib import Path

expected = [
    "dev/verify_phase_6b.sh",
    "dev/verify_phase_6c.sh",
    "dev/verify_phase_6d0.sh",
    "dev/verify_phase_6d1.sh",
    "dev/verify_phase_6d2.sh",
    "dev/verify_phase_6e1.sh",
    "dev/verify_phase_6e2.sh",
    "dev/verify_phase_6e3.sh",
    "dev/verify_phase_6e4.sh",
    "dev/verify_phase_6f2.sh",
    "dev/verify_phase_6f3.sh",
    "dev/verify_phase_6f4.sh",
    "dev/verify_phase_6f5.sh",
    "dev/verify_phase_6f7.sh",
    "dev/verify_phase_7a1.sh",
    "dev/verify_phase_7a2.sh",
    "dev/verify_phase_7a3.sh",
    "dev/verify_phase_7a4.sh",
    "dev/verify_phase_7a5.sh",
    "dev/verify_phase_7a6.sh",
    "dev/verify_phase_7a7.sh",
    "dev/verify_phase_7a8.sh",
    "dev/verify_phase_7b1.sh",
    "dev/verify_phase_7b2.sh",
]

actual = [
    line.strip()
    for line in Path(
        "dev/verification/manifests/knowledge.manifest"
    ).read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
]

assert actual == expected
PY

check \
    "Genesis manifest preserves constitutional order" \
    "$PYTHON_BIN" - <<'PY'
from pathlib import Path

expected = [
    "dev/verify_genesis_1a1.sh",
    "dev/verify_genesis_1a2.sh",
    "dev/verify_genesis_1a3.sh",
    "dev/verify_genesis_2a1.sh",
    "dev/verify_genesis_2a2.sh",
    "dev/verify_reasoning_fixtures.sh",
    "dev/verify_genesis_2a3.sh",
    "dev/verify_genesis_2a3a.sh",
]

actual = [
    line.strip()
    for line in Path(
        "dev/verification/manifests/genesis.manifest"
    ).read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.strip().startswith("#")
]

assert actual == expected
PY

check \
    "Master verifier delegates only to domain orchestrators" \
    "$PYTHON_BIN" - <<'PY'
from pathlib import Path

text = Path("dev/verify_all.sh").read_text(encoding="utf-8")

assert "run_domain ./dev/verify_knowledge_all.sh" in text
assert "run_domain ./dev/verify_genesis_all.sh" in text
assert "run_suite ./dev/verify_phase_" not in text
assert "run_suite ./dev/verify_genesis_" not in text
PY

check \
    "Existing Python verification package remains intact" \
    bash -c '
        test -f dev/verification/__init__.py &&
        test -f dev/verification/models.py &&
        test -f dev/verification/registry.py &&
        test -f dev/verification/runner.py
    '

check \
    "Architecture documentation exists" \
    test -f \
    docs/architecture/genesis/reasoning/GENESIS_II_A3A_VERIFICATION_ARCHITECTURE.md

echo "----------------------------------------------------------------------"
echo "Checks passed : ${PASSED}"
echo "Checks failed : ${FAILED}"

if [[ "${FAILED}" -eq 0 ]]; then
    echo "Overall status: EXCELLENT"
    echo "======================================================================"
    exit 0
fi

echo "Overall status: FAILED"
echo "======================================================================"
exit 1
