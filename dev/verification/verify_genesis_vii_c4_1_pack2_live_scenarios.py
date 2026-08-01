from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.certification import (  # noqa: E402
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


def resolve_ratification_directory() -> Path:
    candidates = (
        PROJECT_ROOT / "artifacts/audit/km0000-c3",
        PROJECT_ROOT / "artifacts/audit/km0000-c3-ratification",
        PROJECT_ROOT / "artifacts/audit/constitutional-ratification",
    )
    for candidate in candidates:
        if (
            (candidate / "constitutional_ratification.json").is_file()
            and (candidate / "constitutional_registry.json").is_file()
        ):
            return candidate
    raise FileNotFoundError(
        "Unable to locate the Genesis VII-C3 ratification artifacts. "
        "Expected constitutional_ratification.json and constitutional_registry.json "
        "under artifacts/audit/km0000-c3."
    )


def main() -> int:
    print("=" * 76)
    print("GENESIS VII-C4.1 PACK 2 — LIVE CONSTITUTIONAL SCENARIO CERTIFICATION")
    print("=" * 76)

    ratification_directory = resolve_ratification_directory()
    c4_summary_path = (
        PROJECT_ROOT
        / "artifacts/audit/km0000-c4/constitutional_compliance.json"
    )
    c4_summary = load_json(c4_summary_path)
    compliance_fingerprint = str(c4_summary.get("compliance_fingerprint", ""))

    engine = ConstitutionalCertificationEngine()
    first = engine.assess_live_scenarios(
        ratification_directory=ratification_directory,
        compliance_fingerprint=compliance_fingerprint,
    )
    second = engine.assess_live_scenarios(
        ratification_directory=ratification_directory,
        compliance_fingerprint=compliance_fingerprint,
    )

    failures = 0
    failures += check(
        bool(first.repository_fingerprint),
        "Repository fingerprint linked",
        first.repository_fingerprint,
    )
    failures += check(
        bool(first.extraction_fingerprint),
        "Extraction fingerprint linked",
        first.extraction_fingerprint,
    )
    failures += check(
        bool(first.analysis_fingerprint),
        "Analysis fingerprint linked",
        first.analysis_fingerprint,
    )
    failures += check(
        bool(first.ratification_fingerprint),
        "Ratification fingerprint linked",
        first.ratification_fingerprint,
    )
    failures += check(
        bool(first.compliance_fingerprint),
        "Compliance fingerprint linked",
        first.compliance_fingerprint,
    )
    failures += check(
        first.certification_fingerprint == second.certification_fingerprint,
        "Live certification is deterministic",
        first.certification_fingerprint,
    )
    failures += check(
        first.statistics.scenarios == 4,
        "Four live constitutional scenarios executed",
        f"scenarios={first.statistics.scenarios}",
    )
    failures += check(
        first.statistics.passed == 4,
        "All live scenarios passed",
        f"passed={first.statistics.passed}",
    )
    failures += check(
        first.statistics.failed == 0,
        "No live scenarios failed",
        f"failed={first.statistics.failed}",
    )
    failures += check(
        first.statistics.skipped == 0,
        "No live scenarios skipped",
        f"skipped={first.statistics.skipped}",
    )
    failures += check(
        first.statistics.positive_findings >= 1,
        "Positive compliance finding demonstrated",
        f"findings={first.statistics.positive_findings}",
    )
    failures += check(
        first.statistics.negative_findings >= 1,
        "Noncompliance finding demonstrated",
        f"findings={first.statistics.negative_findings}",
    )
    failures += check(
        first.statistics.review_findings >= 1,
        "Review-required finding demonstrated",
        f"findings={first.statistics.review_findings}",
    )
    failures += check(
        first.statistics.not_applicable_subjects >= 1,
        "Not-applicable subject demonstrated",
        f"subjects={first.statistics.not_applicable_subjects}",
    )
    failures += check(
        all(
            result.rank == 1
            for result in first.results
            if result.observed_status != "not_applicable"
        ),
        "Expected live article ranks first",
    )
    failures += check(
        all(result.traceability_complete for result in first.results),
        "Live scenario traceability complete",
    )
    failures += check(
        not first.diagnostics,
        "Certification policy diagnostics clear",
        f"diagnostics={len(first.diagnostics)}",
    )

    output_dir = PROJECT_ROOT / "artifacts/audit/km0000-c4_1-pack2"
    written = ConstitutionalCertificationReporter().write(first, output_dir)
    expected = {
        "constitutional_certification.json",
        "constitutional_certification_policy.json",
        "constitutional_certification_scenarios.json",
        "constitutional_certification_traceability.json",
        "constitutional_certification_report.md",
    }
    failures += check(
        {path.name for path in written} == expected,
        "Canonical Pack 2 artifact set",
        f"files={len(written)}",
    )

    invalid = []
    for path in written:
        if path.suffix == ".json":
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                invalid.append(path.name)
    failures += check(
        not invalid,
        "Pack 2 JSON artifacts valid",
        f"invalid={len(invalid)}",
    )

    print("-" * 76)
    print(f"Ratification directory     : {ratification_directory}")
    print(f"Repository fingerprint     : {first.repository_fingerprint}")
    print(f"Extraction fingerprint     : {first.extraction_fingerprint}")
    print(f"Analysis fingerprint       : {first.analysis_fingerprint}")
    print(f"Ratification fingerprint   : {first.ratification_fingerprint}")
    print(f"Compliance fingerprint     : {first.compliance_fingerprint}")
    print(f"Certification fingerprint  : {first.certification_fingerprint}")
    print(f"Live scenarios             : {first.statistics.scenarios}")
    print(f"Passed                     : {first.statistics.passed}")
    print(f"Failed                     : {first.statistics.failed}")
    print(f"Positive findings          : {first.statistics.positive_findings}")
    print(f"Negative findings          : {first.statistics.negative_findings}")
    print(f"Review findings            : {first.statistics.review_findings}")
    print(f"Not-applicable subjects    : {first.statistics.not_applicable_subjects}")
    print(f"Diagnostics                : {first.statistics.diagnostics}")
    print("-" * 76)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 76)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
