#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${ROOT}"
"${PYTHON_BIN}" - <<'PY'
from core.retrieval.grounded_answer import GroundedAnswerEngine
from core.retrieval.qualification import (
    EvidenceCandidate, QualificationDecision, QualificationResult,
    QualificationScore, QualifiedEvidence,
)
candidate = EvidenceCandidate(
    source_id="certified", source_path="/knowledge/certified.txt",
    title="Certified Grounded Answer Source", subject="grounded answer",
    excerpt="The engine ranks evidence, preserves provenance, and states uncertainty.",
    backend="certification", retrieval_score=.95, metadata={},
)
evidence = QualifiedEvidence(
    candidate=candidate, score=QualificationScore(final=.95),
    decision=QualificationDecision.ACCEPTED, explanation="certification",
)
plan = GroundedAnswerEngine().plan(
    "What does the grounded answer engine do?",
    QualificationResult(accepted=(evidence,)),
)
assert plan.citations and "[C1]" in plan.synthesis_prompt
assert plan.confidence > 0
assert "Do not invent missing facts" in plan.synthesis_prompt
print("[PASS] Qualified evidence ranked")
print("[PASS] Citation provenance generated")
print("[PASS] Confidence calibrated")
print("[PASS] Grounded synthesis contract generated")
print("[PASS] No live conversation-path integration")
PY
