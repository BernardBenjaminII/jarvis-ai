from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.governance.constitution.coverage.graph.directorate_public_api import (  # noqa: E402
    CANONICAL_DIRECTORATES,
    ConstitutionalDirectorateFoundationEngine,
    DirectorateNodeKind,
)


def check(condition: bool, label: str, detail: str = "") -> int:
    status = "PASS" if condition else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")
    return 0 if condition else 1


def main() -> int:
    print("=" * 78)
    print("GENESIS VII-C4.3 PACK 3B-2B.1 — DIRECTORATE FOUNDATION")
    print("=" * 78)

    source = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3b2a"
    engine = ConstitutionalDirectorateFoundationEngine()
    first = engine.assess(pack3b2a_directory=source)
    second = engine.assess(pack3b2a_directory=source)

    failures = 0
    failures += check(
        bool(first.article_intelligence_fingerprint),
        "Article intelligence fingerprint preserved",
        first.article_intelligence_fingerprint,
    )
    failures += check(
        bool(first.graph_foundation_fingerprint),
        "Graph foundation fingerprint preserved",
        first.graph_foundation_fingerprint,
    )
    failures += check(
        bool(first.authority_graph_fingerprint),
        "Authority graph fingerprint preserved",
        first.authority_graph_fingerprint,
    )
    failures += check(
        bool(first.repository_projection_fingerprint),
        "Repository projection fingerprint linked",
        first.repository_projection_fingerprint,
    )
    failures += check(
        first.directorate_foundation_fingerprint
        == second.directorate_foundation_fingerprint,
        "Directorate foundation deterministic",
        first.directorate_foundation_fingerprint,
    )

    directorates = [
        node
        for node in first.nodes
        if node.node_kind is DirectorateNodeKind.DIRECTORATE
    ]
    responsibilities = [
        node
        for node in first.nodes
        if node.node_kind is DirectorateNodeKind.RESPONSIBILITY
    ]
    domains = [
        node
        for node in first.nodes
        if node.node_kind is DirectorateNodeKind.OWNERSHIP_DOMAIN
    ]

    failures += check(
        len(directorates) == len(CANONICAL_DIRECTORATES),
        "Canonical directorates established",
        f"directorates={len(directorates)}",
    )
    failures += check(
        len(responsibilities) == len(CANONICAL_DIRECTORATES),
        "Canonical responsibilities established",
        f"responsibilities={len(responsibilities)}",
    )
    failures += check(
        bool(domains),
        "Repository ownership domains projected",
        f"domains={len(domains)}",
    )
    failures += check(
        first.integrity.is_valid,
        "Directorate foundation integrity verified",
        f"diagnostics={len(first.integrity.diagnostics)}",
    )
    failures += check(
        not first.integrity.duplicate_node_ids,
        "Directorate node identifiers unique",
    )
    failures += check(
        not first.integrity.duplicate_edge_ids,
        "Directorate edge identifiers unique",
    )
    failures += check(
        not first.integrity.dangling_edge_ids,
        "No dangling directorate edges",
    )
    failures += check(
        not first.integrity.missing_directorate_keys,
        "No canonical directorates missing",
    )
    failures += check(
        not first.integrity.invalid_edge_ids,
        "Directorate edge semantics valid",
    )
    failures += check(
        not first.integrity.orphan_responsibility_ids,
        "No orphan responsibilities",
    )
    failures += check(
        not first.diagnostics,
        "Directorate foundation diagnostics clear",
        f"diagnostics={len(first.diagnostics)}",
    )

    output = PROJECT_ROOT / "artifacts/audit/km0000-c4_3-pack3b2b1"
    output.mkdir(parents=True, exist_ok=True)
    output_file = output / "constitutional_directorate_foundation.json"
    output_file.write_text(
        json.dumps(first.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    failures += check(
        output_file.exists(),
        "Canonical Pack 3B-2B.1 artifact written",
        output_file.name,
    )
    try:
        json.loads(output_file.read_text(encoding="utf-8"))
        valid_json = True
    except json.JSONDecodeError:
        valid_json = False
    failures += check(valid_json, "Pack 3B-2B.1 JSON artifact valid")

    print("-" * 78)
    print(f"Article intelligence fp  : {first.article_intelligence_fingerprint}")
    print(f"Graph foundation fp      : {first.graph_foundation_fingerprint}")
    print(f"Authority graph fp       : {first.authority_graph_fingerprint}")
    print(f"Repository projection fp : {first.repository_projection_fingerprint}")
    print(f"Directorate foundation fp: {first.directorate_foundation_fingerprint}")
    print(f"Directorates             : {len(directorates)}")
    print(f"Responsibilities         : {len(responsibilities)}")
    print(f"Ownership domains        : {len(domains)}")
    print(f"Integrity valid          : {first.integrity.is_valid}")
    print(f"Diagnostics              : {len(first.diagnostics)}")
    print("-" * 78)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 78)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
