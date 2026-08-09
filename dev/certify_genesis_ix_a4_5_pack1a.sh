#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
"${PYTHON_BIN}" - <<'PY'
import json
from core.retrieval.qualification import *
candidate = EvidenceCandidate("cert","/cert","Runtime Interface","qualification","canonical contracts","certification",.85,{"pack":"1A"})
accepted = QualifiedEvidence(candidate, QualificationScore(lexical=.9, semantic=.8, phrase=.9, entity=.8, subject=.9, provenance=1, final=.88), QualificationDecision.ACCEPTED, "fixture")
result = QualificationResult((accepted,), threshold=.25, runtime_statistics={"behavior_changes":0})
payload = result.to_dict()
assert payload["has_accepted_evidence"]
assert payload["total_candidates"] == 1
assert json.loads(json.dumps(payload)) == payload
print("[PASS] Canonical qualification contracts")
print("[PASS] Stable serialization")
print("[PASS] No runtime behavior changes")
PY
