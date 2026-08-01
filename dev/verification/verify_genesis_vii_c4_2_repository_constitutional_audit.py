from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.repository_audit import (  # noqa: E402
    RepositoryConstitutionalAuditEngine,
    RepositoryConstitutionalAuditReporter,
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
        "Unable to locate Genesis VII-C3 ratification artifacts."
    )


def main() -> int:
    print("=" * 78)
    print("GENESIS VII-C4.2 — REPOSITORY-WIDE CONSTITUTIONAL AUDIT")
    print("=" * 78)

    ratification_directory = resolve_ratification_directory()
    compliance_summary = load_json(
        PROJECT_ROOT
        / "artifacts/audit/km0000-c4/constitutional_compliance.json"
    )
    certification_summary = load_json(
        PROJECT_ROOT
        / "artifacts/audit/km0000-c4_1-pack2/constitutional_certification.json"
    )

    engine = RepositoryConstitutionalAuditEngine()
    kwargs = {
        "repository_root": PROJECT_ROOT,
        "ratification_directory": ratification_directory,
        "compliance_fingerprint": str(
            compliance_summary.get("compliance_fingerprint", "")
        ),
        "certification_fingerprint": str(
            certification_summary.get("certification_fingerprint", "")
        ),
    }
    first = engine.assess(**kwargs)
    second = engine.assess(**kwargs)

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
        bool(first.certification_fingerprint),
        "Certification fingerprint linked",
        first.certification_fingerprint,
    )
    failures += check(
        first.audit_fingerprint == second.audit_fingerprint,
        "Repository audit is deterministic",
        first.audit_fingerprint,
    )
    failures += check(
        first.statistics.artifacts_discovered > 0,
        "Repository artifacts discovered",
        f"artifacts={first.statistics.artifacts_discovered}",
    )
    failures += check(
        first.statistics.artifacts_discovered
        == first.statistics.artifacts_evaluated,
        "Every discovered artifact evaluated",
        f"evaluated={first.statistics.artifacts_evaluated}",
    )
    failures += check(
        len({item.artifact_id for item in first.artifacts})
        == len(first.artifacts),
        "Artifact identifiers unique",
    )
    failures += check(
        len({item["finding_id"] for item in first.findings})
        == len(first.findings),
        "Finding identifiers unique",
    )
    failures += check(
        first.statistics.articles_referenced
        + first.statistics.articles_unused
        == first.statistics.articles_considered,
        "Every constitutional article accounted for",
        f"articles={first.statistics.articles_considered}",
    )
    failures += check(
        len(first.article_usage) == first.statistics.articles_considered,
        "Article usage registry complete",
        f"usage_records={len(first.article_usage)}",
    )
    failures += check(
        not first.diagnostics,
        "Repository audit diagnostics clear",
        f"diagnostics={len(first.diagnostics)}",
    )

    output_dir = PROJECT_ROOT / "artifacts/audit/km0000-c4_2"
    written = RepositoryConstitutionalAuditReporter().write(first, output_dir)
    expected = {
        "constitutional_repository_inventory.json",
        "constitutional_repository_audit.json",
        "constitutional_repository_statistics.json",
        "constitutional_article_usage.json",
        "constitutional_article_heatmap.json",
        "constitutional_repository_traceability.json",
        "constitutional_repository_findings.json",
        "constitutional_repository_report.md",
    }
    failures += check(
        {path.name for path in written} == expected,
        "Canonical C4.2 artifact set",
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
        "C4.2 JSON artifacts valid",
        f"invalid={len(invalid)}",
    )

    s = first.statistics
    print("-" * 78)
    print(f"Repository root            : {first.repository_root}")
    print(f"Repository fingerprint     : {first.repository_fingerprint}")
    print(f"Extraction fingerprint     : {first.extraction_fingerprint}")
    print(f"Analysis fingerprint       : {first.analysis_fingerprint}")
    print(f"Ratification fingerprint   : {first.ratification_fingerprint}")
    print(f"Compliance fingerprint     : {first.compliance_fingerprint}")
    print(f"Certification fingerprint  : {first.certification_fingerprint}")
    print(f"Audit fingerprint          : {first.audit_fingerprint}")
    print(f"Artifacts discovered       : {s.artifacts_discovered}")
    print(f"Artifacts evaluated        : {s.artifacts_evaluated}")
    print(f"Applicable artifacts       : {s.applicable_artifacts}")
    print(f"Compliant artifacts        : {s.compliant_artifacts}")
    print(f"Review-required artifacts  : {s.review_required_artifacts}")
    print(f"Noncompliant artifacts     : {s.noncompliant_artifacts}")
    print(f"Not-applicable artifacts   : {s.not_applicable_artifacts}")
    print(f"Findings                   : {s.findings}")
    print(f"Articles considered        : {s.articles_considered}")
    print(f"Articles referenced        : {s.articles_referenced}")
    print(f"Articles unused            : {s.articles_unused}")
    print(f"Diagnostics                : {len(first.diagnostics)}")
    print("-" * 78)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 78)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
