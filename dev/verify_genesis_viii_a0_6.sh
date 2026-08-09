#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

passed=0
failed=0

run_check() {
    local label="$1"
    shift
    if "$@"; then
        printf '[PASS] %s\n' "${label}"
        passed=$((passed + 1))
    else
        printf '[FAIL] %s\n' "${label}"
        failed=$((failed + 1))
    fi
}

printf '%s\n' '========================================================================'
printf '%s\n' 'JARVIS — GENESIS VIII-A0-6'
printf '%s\n' 'GOVERNMENT FRAMEWORK CERTIFICATION'
printf '%s\n' '========================================================================'

for index in 1 2 3 4 5; do
    run_check "VIII-A0-${index} prerequisite" \
        env PYTHON_BIN="${PYTHON_BIN}" "./dev/verify_genesis_viii_a0_${index}.sh"
done

run_check "Certification package compilation" \
    "${PYTHON_BIN}" -m py_compile \
        dev/tools/audit_government_framework.py \
        tests/test_genesis_viii_a0_6_government_framework_certification.py

run_check "Certification unit tests" \
    "${PYTHON_BIN}" -m unittest -v \
        tests.test_genesis_viii_a0_6_government_framework_certification

run_check "Repository-derived Government Framework audit" \
    "${PYTHON_BIN}" dev/tools/audit_government_framework.py

run_check "Certification JSON generated" \
    test -s artifacts/audit/government_framework_certification.json

run_check "Certification Markdown generated" \
    test -s artifacts/audit/government_framework_certification.md

run_check "Government Framework fingerprint generated" \
    test -s artifacts/audit/government_framework.sha256

run_check "Certification artifacts reproducible" \
    "${PYTHON_BIN}" - <<'PY'
from pathlib import Path
import hashlib
import os
import subprocess

paths = (
    Path("artifacts/audit/government_framework_certification.json"),
    Path("artifacts/audit/government_framework_certification.md"),
    Path("artifacts/audit/government_framework.sha256"),
)
before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
subprocess.run(
    [os.environ.get("PYTHON_BIN", "python"), "dev/tools/audit_government_framework.py"],
    check=True,
    stdout=subprocess.DEVNULL,
)
after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
assert before == after
PY

printf '%s\n' '------------------------------------------------------------------------'
printf 'Checks passed : %d\n' "${passed}"
printf 'Checks failed : %d\n' "${failed}"
if [[ ${failed} -eq 0 ]]; then
    printf '%s\n' 'Overall status: EXCELLENT'
else
    printf '%s\n' 'Overall status: FAILED'
fi
printf '%s\n' '========================================================================'

[[ ${failed} -eq 0 ]]
