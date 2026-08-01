from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.analysis import (  # noqa: E402
    ANALYSIS_SCHEMA_VERSION,
    ConstitutionalAnalysisEngine,
    ConstitutionalAnalysisReporter,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def main() -> int:
    print("=" * 72)
    print("GENESIS VII-C2 — CONSTITUTIONAL ANALYSIS ENGINE")
    print("=" * 72)

    extraction_dir = PROJECT_ROOT / "artifacts/audit/km0000-c1"
    output_dir = PROJECT_ROOT / "artifacts/audit/km0000-c2"

    failures = 0
    engine = ConstitutionalAnalysisEngine()
    first = engine.analyze(extraction_dir)
    second = engine.analyze(extraction_dir)

    failures += check(first.schema_version == ANALYSIS_SCHEMA_VERSION, "Analysis schema is supported", first.schema_version)
    failures += check(bool(first.repository_fingerprint), "C1 repository fingerprint available", first.repository_fingerprint)
    failures += check(bool(first.extraction_fingerprint), "C1 extraction fingerprint available", first.extraction_fingerprint)
    failures += check(first.analysis_fingerprint == second.analysis_fingerprint, "Analysis is deterministic", first.analysis_fingerprint)

    claim_ids = [claim.claim_id for claim in first.claims]
    rel_ids = [relationship.relationship_id for relationship in first.relationships]
    rel_keys = [
        (r.source_claim_id, r.target_claim_id, r.relationship_type, r.relationship_id)
        for r in first.relationships
    ]

    failures += check(len(claim_ids) == len(set(claim_ids)), "Claim identifiers are unique", f"count={len(claim_ids)}")
    failures += check(len(rel_ids) == len(set(rel_ids)), "Relationship identifiers are unique", f"count={len(rel_ids)}")
    failures += check(rel_keys == sorted(rel_keys), "Relationships use deterministic ordering", f"count={len(rel_keys)}")
    failures += check(
        all(r.source_claim_id in set(claim_ids) and r.target_claim_id in set(claim_ids) for r in first.relationships),
        "Every relationship references existing claims",
        f"relationships={len(first.relationships)}",
    )

    written = ConstitutionalAnalysisReporter().write(first, output_dir)
    expected_names = {
        "constitutional_analysis.json",
        "constitutional_graph.json",
        "constitutional_conflicts.json",
        "constitutional_duplicates.json",
        "constitutional_concordance.json",
        "constitutional_authority.json",
        "constitutional_analysis_report.md",
    }
    failures += check({p.name for p in written} == expected_names, "Canonical C2 artifact set", f"files={len(written)}")

    invalid = []
    for path in written:
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid.append(path.name)
    failures += check(not invalid, "C2 JSON artifacts are valid", f"invalid={len(invalid)}")

    s = first.statistics
    print("-" * 72)
    print(f"Repository fingerprint : {first.repository_fingerprint}")
    print(f"Extraction fingerprint : {first.extraction_fingerprint}")
    print(f"Analysis fingerprint   : {first.analysis_fingerprint}")
    print(f"Claims                 : {s.claims}")
    print(f"Relationships          : {s.relationships}")
    print(f"Duplicates             : {s.duplicates}")
    print(f"Supports               : {s.supports}")
    print(f"Contradictions         : {s.contradictions}")
    print(f"Refinements            : {s.refines}")
    print(f"Authority resolutions  : {s.authority_resolutions}")
    print(f"Diagnostics            : {s.diagnostics}")
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
