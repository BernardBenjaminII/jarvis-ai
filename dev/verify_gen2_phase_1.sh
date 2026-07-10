#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "======================================================================"
echo "JARVIS GEN 2 PHASE I VERIFICATION"
echo "======================================================================"

echo
echo "[1/6] Python version"
"$PYTHON_BIN" --version

echo
echo "[2/6] Compile executive package"
"$PYTHON_BIN" -m compileall -q core/executive

echo
echo "[3/6] Import surface"
"$PYTHON_BIN" - <<'PY'
from core.executive import (
    DirectorRegistry,
    ExecutiveDirector,
    MissionEngine,
    MissionPlanner,
    MissionStore,
)

print("Executive imports: PASS")
PY

echo
echo "[4/6] Unit tests"
"$PYTHON_BIN" -m unittest -v tests.test_gen2_executive

echo
echo "[5/6] CLI smoke test"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$PYTHON_BIN" -m core.executive.cli \
    --db "$TMP_DIR/missions.sqlite3" \
    submit \
    "Search the knowledge catalog for the JARVIS architecture" \
    > "$TMP_DIR/result.json"

"$PYTHON_BIN" - "$TMP_DIR/result.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

assert data["status"] == "completed", data
assert len(data["tasks"]) >= 3, data
assert any(task["director"] == "knowledge" for task in data["tasks"]), data

print("CLI smoke test: PASS")
print(f"Mission ID: {data['mission_id']}")
print(f"Tasks     : {len(data['tasks'])}")
print(f"Status    : {data['status']}")
PY

echo
echo "[6/6] Working tree summary"
git status --short

echo
echo "======================================================================"
echo "GEN 2 PHASE I: PASS"
echo "Executive Director + Mission Engine are operational."
echo "======================================================================"
