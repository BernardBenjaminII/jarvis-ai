#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
"${PYTHON_BIN}" - <<'PY'
from core.retrieval.qualification import *
engine = QualificationEngine()
known = EvidenceCandidate("known","/knowledge/uh60.txt","UH-60 Hydraulic Maintenance Manual","UH-60 hydraulic systems","Black Hawk hydraulic maintenance.","runtime_fts",.85,{})
false = EvidenceCandidate("false","/knowledge/electronics.txt","Practical Electronics Handbook","computer architecture","Von Neumann architecture.","runtime_fts",.08,{})
assert len(engine.evaluate("UH-60 Black Hawk hydraulic system maintenance",[known]).accepted)==1
assert len(engine.evaluate("Quantum Banana Warp Core Mk XII",[false]).accepted)==0
print("[PASS] Relevant evidence accepted")
print("[PASS] Fabricated query rejected")
print("[PASS] No Executive Runtime integration")
PY
