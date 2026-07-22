#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

"${PYTHON_BIN}" -m core.engineering.cli bootstrap-manifest \
    --project-root "${PROJECT_ROOT}" \
    --tests-root tests \
    --output dev/verification/manifests/test_public_api_expectations.json

set +e
"${PYTHON_BIN}" -m core.engineering.cli analyze \
    --project-root "${PROJECT_ROOT}" \
    --manifest dev/verification/manifests/test_public_api_expectations.json \
    --json-output .artifacts/engineering/public_api_compatibility.json \
    --report-output docs/audits/public_api_compatibility_report.md
status=$?
set -e

if [ "${status}" -eq 2 ]; then
    echo
    echo "Compatibility analysis completed successfully."
    echo "Restoration findings are present; review:"
    echo "  docs/audits/public_api_compatibility_report.md"
    exit 0
fi

exit "${status}"
