from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.coverage.graph.directorate_projection_public_api import (  # noqa: E402
    ConstitutionalDirectorateProjectionEngine,
    ConstitutionalDirectorateProjectionReporter,
    ConstitutionalDirectorateQueryService,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def main() -> int:
    print("=" * 78)
    print("GENESIS VII-C4.3 PACK 3B-2B.2 — DIRECTORATE PROJECTION")
    print("=" * 78)

    source = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3b2b1"
    engine = ConstitutionalDirectorateProjectionEngine()
    first = engine.assess(pack3b2b1_directory=source)
    second = engine.assess(pack3b2b1_directory=source)

    failures = 0
    for label, key in (
        ("Article intelligence fingerprint preserved", "article_intelligence_fingerprint"),
        ("Graph foundation fingerprint preserved", "graph_foundation_fingerprint"),
        ("Authority graph fingerprint preserved", "authority_graph_fingerprint"),
        ("Repository projection fingerprint preserved", "repository_projection_fingerprint"),
        ("Directorate foundation fingerprint linked", "directorate_foundation_fingerprint"),
    ):
        failures += check(bool(first[key]), label, str(first[key]))

    failures += check(
        first["directorate_projection_fingerprint"]
        == second["directorate_projection_fingerprint"],
        "Directorate projection deterministic",
        str(first["directorate_projection_fingerprint"]),
    )

    metrics = first["metrics"]
    failures += check(
        metrics["ownership_completeness_ratio"] == 1.0,
        "Organizational ownership complete",
        f"ratio={metrics['ownership_completeness_ratio']:.2%}",
    )
    failures += check(
        not metrics["unowned_domain_ids"],
        "No unowned repository domains",
        f"unowned={len(metrics['unowned_domain_ids'])}",
    )

    query = ConstitutionalDirectorateQueryService(first["graph"])
    failures += check(
        query.directorates() == query.directorates(),
        "Directorate query layer deterministic",
    )
    failures += check(
        not query.unowned_domains(),
        "Ownership query confirms complete assignment",
    )
    failures += check(
        not first["diagnostics"],
        "Directorate projection diagnostics clear",
        f"diagnostics={len(first['diagnostics'])}",
    )

    output = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3b2b2"
    written = ConstitutionalDirectorateProjectionReporter().write(first, output)
    expected = {
        "constitutional_directorate_projection.json",
        "constitutional_directorate_nodes.json",
        "constitutional_directorate_edges.json",
        "constitutional_directorate_metrics.json",
        "constitutional_directorate_integrity.json",
        "constitutional_directorate_summary.md",
    }
    failures += check(
        {path.name for path in written} == expected,
        "Canonical Pack 3B-2B.2 artifact set",
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
        "Pack 3B-2B.2 JSON artifacts valid",
        f"invalid={len(invalid)}",
    )

    print("-" * 78)
    print(f"Article intelligence fp    : {first['article_intelligence_fingerprint']}")
    print(f"Graph foundation fp        : {first['graph_foundation_fingerprint']}")
    print(f"Authority graph fp         : {first['authority_graph_fingerprint']}")
    print(f"Repository projection fp   : {first['repository_projection_fingerprint']}")
    print(f"Directorate foundation fp  : {first['directorate_foundation_fingerprint']}")
    print(f"Directorate projection fp  : {first['directorate_projection_fingerprint']}")
    print(f"Ownership domains          : {metrics['ownership_domain_count']}")
    print(f"Owned domains              : {metrics['owned_domain_count']}")
    print(f"Unowned domains            : {len(metrics['unowned_domain_ids'])}")
    print(f"Ownership completeness     : {metrics['ownership_completeness_ratio']:.2%}")
    print(f"Diagnostics                : {len(first['diagnostics'])}")
    print("-" * 78)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 78)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
