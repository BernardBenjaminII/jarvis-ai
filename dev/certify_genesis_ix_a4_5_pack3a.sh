#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"

"${PYTHON_BIN}" -m dev.certification.repair_genesis_ix_a4_5_pack3a

"${PYTHON_BIN}" - <<'PY'
from core.src.routes.api import conversation_service
from core.conversation.contracts import ExecutiveRequestContext
from core.knowledge_catalog.qualified_search import get_last_qualification_trace

query = "internal architecture of the Quantum Banana Warp Core Mk XII"
objectives = conversation_service.compiler.compile(query)
context = ExecutiveRequestContext.create(
    operator_input=query,
    mode="full",
    channel="text",
    metadata={"certification": "genesis_ix_a4_5_pack3a"},
    objectives=objectives,
)
grounding = conversation_service.orchestrator.grounding_service.ground(context)
payload = grounding.to_dict()
trace = get_last_qualification_trace()

assert payload["status"] == "gap", payload
assert payload["gap_count"] >= 1, payload
assert trace is not None
assert trace["accepted_count"] == 0
assert trace["rejected_count"] >= 1

print("[PASS] Fabricated query rejected by qualification")
print("[PASS] Grounding produces KnowledgeGap")
print("[PASS] Qualification diagnostics available")
print("[PASS] Executive public APIs unchanged")
PY
