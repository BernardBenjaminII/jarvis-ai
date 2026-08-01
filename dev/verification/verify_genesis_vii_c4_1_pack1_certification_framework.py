from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.certification import (  # noqa: E402
    CERTIFICATION_SCHEMA_VERSION,
    ConstitutionalCertificationEngine,
    ConstitutionalCertificationReporter,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 72)
    print("GENESIS VII-C4.1 PACK 1 — CONSTITUTIONAL CERTIFICATION FRAMEWORK")
    print("=" * 72)

    c4_dir = PROJECT_ROOT / "artifacts/audit/km0000-c4"
    c4_summary = load_json(c4_dir / "constitutional_compliance.json")

    engine = ConstitutionalCertificationEngine()
    kwargs = {
        "repository_fingerprint": str(c4_summary.get("repository_fingerprint", "")),
        "extraction_fingerprint": str(c4_summary.get("extraction_fingerprint", "")),
        "analysis_fingerprint": str(c4_summary.get("analysis_fingerprint", "")),
        "ratification_fingerprint": str(c4_summary.get("ratification_fingerprint", "")),
        "compliance_fingerprint": str(c4_summary.get("compliance_fingerprint", "")),
    }
    first = engine.assess_framework(**kwargs)
    second = engine.assess_framework(**kwargs)

    failures = 0
    failures += check(first.schema_version == CERTIFICATION_SCHEMA_VERSION, "Certification schema is supported", first.schema_version)
    failures += check(bool(first.repository_fingerprint), "Repository fingerprint linked", first.repository_fingerprint)
    failures += check(bool(first.extraction_fingerprint), "Extraction fingerprint linked", first.extraction_fingerprint)
    failures += check(bool(first.analysis_fingerprint), "Analysis fingerprint linked", first.analysis_fingerprint)
    failures += check(bool(first.ratification_fingerprint), "Ratification fingerprint linked", first.ratification_fingerprint)
    failures += check(bool(first.compliance_fingerprint), "Compliance fingerprint linked", first.compliance_fingerprint)
    failures += check(
        first.certification_fingerprint == second.certification_fingerprint,
        "Certification framework is deterministic",
        first.certification_fingerprint,
    )

    scenario_ids = [item.scenario_id for item in first.scenarios]
    result_ids = [item.scenario_id for item in first.results]
    failures += check(len(scenario_ids) == len(set(scenario_ids)), "Scenario identifiers are unique", f"count={len(scenario_ids)}")
    failures += check(set(scenario_ids) == set(result_ids), "Every scenario has a result", f"results={len(result_ids)}")
    failures += check(all(item.status == "skipped" for item in first.results), "Pack 1 scenarios are explicitly deferred", f"skipped={first.statistics.skipped}")
    failures += check(first.statistics.failed == 0, "Framework has no failed scenarios", f"failed={first.statistics.failed}")

    output_dir = PROJECT_ROOT / "artifacts/audit/km0000-c4_1-pack1"
    written = ConstitutionalCertificationReporter().write(first, output_dir)
    expected = {
        "constitutional_certification.json",
        "constitutional_certification_policy.json",
        "constitutional_certification_traceability.json",
        "constitutional_certification_report.md",
    }
    failures += check({path.name for path in written} == expected, "Canonical Pack 1 artifact set", f"files={len(written)}")

    invalid = []
    for path in written:
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid.append(path.name)
    failures += check(not invalid, "Pack 1 JSON artifacts are valid", f"invalid={len(invalid)}")

    print("-" * 72)
    print(f"Repository fingerprint    : {first.repository_fingerprint}")
    print(f"Extraction fingerprint    : {first.extraction_fingerprint}")
    print(f"Analysis fingerprint      : {first.analysis_fingerprint}")
    print(f"Ratification fingerprint  : {first.ratification_fingerprint}")
    print(f"Compliance fingerprint    : {first.compliance_fingerprint}")
    print(f"Certification fingerprint : {first.certification_fingerprint}")
    print(f"Scenarios registered      : {first.statistics.scenarios}")
    print(f"Passed                    : {first.statistics.passed}")
    print(f"Failed                    : {first.statistics.failed}")
    print(f"Deferred to Pack 2        : {first.statistics.skipped}")
    print(f"Diagnostics               : {first.statistics.diagnostics}")
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
