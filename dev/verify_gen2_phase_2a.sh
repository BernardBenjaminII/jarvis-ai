#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "======================================================================"
echo "JARVIS GEN 2 PHASE II-A VERIFICATION"
echo "======================================================================"

echo
echo "[1/7] Python version"
"$PYTHON_BIN" --version

echo
echo "[2/7] Compile executive package"
"$PYTHON_BIN" -m compileall -q core/executive

echo
echo "[3/7] Import capability surface"
"$PYTHON_BIN" - <<'PY'
from core.executive import (
    Capability,
    DirectorDescriptor,
    DirectorReadiness,
    DirectorRegistry,
    RoutingDecision,
)
print("Capability imports: PASS")
PY

echo
echo "[4/7] Phase I regression tests"
"$PYTHON_BIN" -m unittest -v tests.test_gen2_executive

echo
echo "[5/7] Phase II-A capability tests"
"$PYTHON_BIN" -m unittest -v tests.test_gen2_capability_routing

echo
echo "[6/7] Capability-routing smoke test"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$PYTHON_BIN" -m core.executive.cli     --db "$TMP_DIR/missions.sqlite3"     submit     "Search the knowledge catalog for the JARVIS mission architecture"     --plan-only     > "$TMP_DIR/mission.json"

"$PYTHON_BIN" - "$TMP_DIR/mission.json" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
specialist_tasks = [
    task
    for task in data["tasks"]
    if "knowledge_search" in task.get("required_capabilities", [])
]

assert data["status"] == "planned", data
assert len(specialist_tasks) == 1, data

task = specialist_tasks[0]
assert task["director"] == "knowledge", task
assert task["routing_evidence"]["selected_director"] == "knowledge", task
assert task["routing_evidence"]["candidates"], task

print("Capability smoke test: PASS")
print(f"Mission ID  : {data['mission_id']}")
print(f"Director    : {task['director']}")
print(f"Capabilities: {', '.join(task['required_capabilities'])}")
print(f"Reason      : {task['routing_evidence']['reason']}")
PY

echo
echo "[7/7] Git working tree"
git status --short

echo
echo "======================================================================"
echo "GEN 2 PHASE II-A: PASS"
echo "Capability-based director routing is operational."
echo "======================================================================"
