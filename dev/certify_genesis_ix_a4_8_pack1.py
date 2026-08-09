from __future__ import annotations
import json
from pathlib import Path

REQUIRED = (
    "README.md", "Campaign.md", "Objectives.md", "TestMethodology.md",
    "AcceptanceCriteria.md", "FailureClassification.md", "OperatorGuide.md",
    "Readiness.md", "ExecutiveReadinessMatrix.md", "CanonicalArtifacts.md",
)

def main() -> int:
    root = Path.cwd().resolve()
    campaign = root / "docs/campaigns/genesis_ix_a4_8"
    checks = []
    for name in REQUIRED:
        path = campaign / name
        ok = path.is_file() and path.stat().st_size > 0
        checks.append({"document": name, "status": "PASS" if ok else "FAIL"})
    failed = [x for x in checks if x["status"] == "FAIL"]
    report = {
        "status": "EXCELLENT" if not failed else "FAILED",
        "checks_executed": len(checks),
        "checks_passed": len(checks) - len(failed),
        "checks_failed": len(failed),
        "checks": checks,
    }
    output = root / "docs/audits/genesis_ix_a4_8_pack1"
    output.mkdir(parents=True, exist_ok=True)
    (output / "headquarters_certification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Genesis IX-A4.8 Pack 1 — Headquarters Certification",
        "",
        f"**Status:** **{report['status']}**",
        f"**Checks passed:** {report['checks_passed']}/{report['checks_executed']}",
    ]
    (output / "headquarters_certification.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("=" * 76)
    print("GENESIS IX-A4.8 PACK 1 — EXECUTIVE ACCEPTANCE HEADQUARTERS")
    print("=" * 76)
    print("Checks executed :", report["checks_executed"])
    print("Checks passed   :", report["checks_passed"])
    print("Checks failed   :", report["checks_failed"])
    print("Overall status  :", report["status"])
    print("=" * 76)
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())
