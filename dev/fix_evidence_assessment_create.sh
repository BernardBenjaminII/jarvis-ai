#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

python3 <<'PY'
from pathlib import Path
import re

path = Path("core/reasoning/evidence/contracts.py")
text = path.read_text()

replacement = '''
    @classmethod
    def create(
        cls,
        *,
        evidence_id: EvidenceId,
        reasoning_context_id: str,
        assessor_id: str,
        method: AssessmentMethod,
        sequence: int,
        rationale: str,
        source_reliability: Decimal | int | str | None = None,
        content_credibility: Decimal | int | str | None = None,
        relevance: Decimal | int | str | None = None,
        freshness: Decimal | int | str | None = None,
        independence: Decimal | int | str | None = None,
        diagnosticity: Decimal | int | str | None = None,
        completeness: Decimal | int | str | None = None,
        consistency: Decimal | int | str | None = None,
        decision_impact: Decimal | int | str | None = None,
    ) -> "EvidenceAssessment":
        """
        Create a canonical EvidenceAssessment.

        Constitutional lifecycle:

            raw input
                ↓
            validation
                ↓
            normalization
                ↓
            canonical payload
                ↓
            deterministic identity
                ↓
            immutable assessment
        """

        #
        # STEP 1
        # Construct a provisional assessment.
        # Validation occurs in __post_init__ before identity generation.
        #

        placeholder_id = EvidenceAssessmentId(
            "evidence-assessment:" + ("0" * 64)
        )

        provisional = cls(
            assessment_id=placeholder_id,
            evidence_id=evidence_id,
            reasoning_context_id=reasoning_context_id,
            assessor_id=assessor_id,
            method=method,
            sequence=sequence,
            rationale=rationale,
            source_reliability=source_reliability,
            content_credibility=content_credibility,
            relevance=relevance,
            freshness=freshness,
            independence=independence,
            diagnosticity=diagnosticity,
            completeness=completeness,
            consistency=consistency,
            decision_impact=decision_impact,
        )

        #
        # STEP 2
        # Build the canonical payload from the validated object.
        #

        payload = {
            "evidence_id": provisional.evidence_id,
            "reasoning_context_id": provisional.reasoning_context_id,
            "assessor_id": provisional.assessor_id,
            "method": provisional.method,
            "sequence": provisional.sequence,
            "rationale": provisional.rationale,
            "source_reliability": provisional.source_reliability,
            "content_credibility": provisional.content_credibility,
            "relevance": provisional.relevance,
            "freshness": provisional.freshness,
            "independence": provisional.independence,
            "diagnosticity": provisional.diagnosticity,
            "completeness": provisional.completeness,
            "consistency": provisional.consistency,
            "decision_impact": provisional.decision_impact,
        }

        #
        # STEP 3
        # Generate deterministic identity.
        #

        canonical_id = EvidenceAssessmentId.from_payload(payload)

        #
        # STEP 4
        # Return immutable assessment.
        #

        return replace(
            provisional,
            assessment_id=canonical_id,
        )
'''

pattern = re.compile(
    r'@classmethod\s+def create\([\s\S]*?return cls\([\s\S]*?\n\s*\)',
    re.MULTILINE,
)

new_text, count = pattern.subn(replacement.strip(), text, count=1)

if count != 1:
    raise SystemExit(
        "ERROR: Unable to locate EvidenceAssessment.create(). "
        "No changes made."
    )

path.write_text(new_text)
print("Updated:", path)
PY

echo
echo "=========================================="
echo "EvidenceAssessment.create() updated"
echo "=========================================="
echo
echo "Run:"
echo
echo "PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \\"
echo "pytest -q tests/test_genesis_2a4_evidence_contracts.py -k float_scores"
echo
echo "Then:"
echo
echo "PYTHON_BIN=/media/abdullah/JARVIS_RUNTIME_L/venvs/ubuntu/bin/python \\"
echo "./dev/verify_genesis_2a4.sh"

