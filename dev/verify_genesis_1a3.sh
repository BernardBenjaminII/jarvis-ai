#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "$PROJECT_ROOT"

echo
echo "======================================================================"
echo "JARVIS GEN 2 — GENESIS I-A3"
echo "KNOWLEDGE INTEGRATION AUDIT"
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

check_file "core/reasoning/knowledge.py"
check_file "core/reasoning/pipeline.py"
check_file \
    "dev/tools/audit_reasoning_knowledge_integration.py"
check_file "dev/verify_genesis_1a3.sh"

if "$PYTHON_BIN" -m py_compile \
    core/reasoning/knowledge.py \
    core/reasoning/pipeline.py \
    dev/tools/audit_reasoning_knowledge_integration.py
then
    pass "Knowledge integration modules compile"
else
    fail "Knowledge integration modules compile"
fi

if "$PYTHON_BIN" \
    dev/tools/audit_reasoning_knowledge_integration.py
then
    pass "Knowledge integration audit generated"
else
    fail "Knowledge integration audit generated"
fi

check_file \
    "docs/architecture/convergence/genesis_1a3_knowledge_integration_audit.json"
check_file \
    "docs/architecture/convergence/genesis_1a3_knowledge_integration_audit.md"

if "$PYTHON_BIN" \
    dev/tools/audit_reasoning_knowledge_integration.py \
    --check
then
    pass "Generated audit reports are deterministic and current"
else
    fail "Generated audit reports are deterministic and current"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

report_path = Path(
    "docs/architecture/convergence/"
    "genesis_1a3_knowledge_integration_audit.json"
)

report = json.loads(
    report_path.read_text(encoding="utf-8")
)

assert report["audit_id"] == "GENESIS-I-A3"

assert report["sources"] == [
    "core/reasoning/knowledge.py",
    "core/reasoning/pipeline.py",
]

knowledge_classes = {
    item["name"]
    for item in report["modules"]["knowledge"]["classes"]
}
pipeline_classes = {
    item["name"]
    for item in report["modules"]["pipeline"]["classes"]
}

assert {
    "KnowledgeEvidenceAdapterError",
    "AdaptedEvidenceBatch",
    "KnowledgeEvidenceAdapter",
}.issubset(knowledge_classes)

assert {
    "KnowledgeReasoningOutcome",
    "KnowledgeReasoningPipeline",
}.issubset(pipeline_classes)

assert (
    report["missing_expected_classes"]["knowledge"]
    == []
)
assert (
    report["missing_expected_classes"]["pipeline"]
    == []
)

assert (
    report["conclusions"]["knowledge_adapter_present"]
    is True
)
assert (
    report["conclusions"]["adapted_batch_contract_present"]
    is True
)
assert (
    report["conclusions"]["knowledge_pipeline_present"]
    is True
)
assert (
    report["conclusions"]["pipeline_outcome_contract_present"]
    is True
)
assert (
    report["conclusions"][
        "expected_knowledge_classes_present"
    ]
    is True
)
assert (
    report["conclusions"][
        "expected_pipeline_classes_present"
    ]
    is True
)

assert len(report["integration_flow"]) >= 7
assert report["architectural_findings"]
assert report["migration_constraints"]

print("[PASS] Canonical knowledge-integration assertions")
PY
then
    pass "Canonical knowledge-integration structure"
else
    fail "Canonical knowledge-integration structure"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import inspect

from core.reasoning.knowledge import (
    AdaptedEvidenceBatch,
    KnowledgeEvidenceAdapter,
    KnowledgeEvidenceAdapterError,
)
from core.reasoning.pipeline import (
    KnowledgeReasoningOutcome,
    KnowledgeReasoningPipeline,
)

assert inspect.isclass(KnowledgeEvidenceAdapterError)
assert inspect.isclass(AdaptedEvidenceBatch)
assert inspect.isclass(KnowledgeEvidenceAdapter)
assert inspect.isclass(KnowledgeReasoningOutcome)
assert inspect.isclass(KnowledgeReasoningPipeline)

adapter_methods = {
    name
    for name, value in inspect.getmembers(
        KnowledgeEvidenceAdapter,
        predicate=inspect.isfunction,
    )
    if not name.startswith("__")
}

pipeline_methods = {
    name
    for name, value in inspect.getmembers(
        KnowledgeReasoningPipeline,
        predicate=inspect.isfunction,
    )
    if not name.startswith("__")
}

assert adapter_methods
assert pipeline_methods

print(
    "[PASS] Knowledge adapter importability: "
    + ", ".join(sorted(adapter_methods))
)
print(
    "[PASS] Knowledge pipeline importability: "
    + ", ".join(sorted(pipeline_methods))
)
PY
then
    pass "Knowledge integration import smoke test"
else
    fail "Knowledge integration import smoke test"
fi

if "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
from pathlib import Path

for relative_path in (
    "core/reasoning/knowledge.py",
    "core/reasoning/pipeline.py",
):
    source_path = Path(relative_path)
    tree = ast.parse(
        source_path.read_text(encoding="utf-8"),
        filename=str(source_path),
    )

    forbidden_calls = {
        "requests.get",
        "requests.post",
        "subprocess.run",
        "subprocess.Popen",
        "os.system",
    }

    discovered: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                discovered.add(
                    f"{node.func.value.id}.{node.func.attr}"
                )

    violations = sorted(
        forbidden_calls.intersection(discovered)
    )

    assert not violations, (
        f"{relative_path} contains prohibited direct external "
        f"operations: {violations}"
    )

print(
    "[PASS] Knowledge integration remains free of direct "
    "network and process execution"
)
PY
then
    pass "Knowledge integration boundary isolation"
else
    fail "Knowledge integration boundary isolation"
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
