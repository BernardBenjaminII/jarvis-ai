from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Standalone entry-point prebootstrap: make the repository importable before
# importing the shared dev.runtime package. All further initialization is
# delegated to bootstrap_runtime().
_ENTRY_ROOT = Path(__file__).resolve().parents[1]
_ENTRY_ROOT_TEXT = str(_ENTRY_ROOT)

if _ENTRY_ROOT_TEXT not in sys.path:
    sys.path.insert(0, _ENTRY_ROOT_TEXT)


from dev.runtime import bootstrap_runtime


RUNTIME = bootstrap_runtime(Path(__file__))
PROJECT_ROOT = RUNTIME.project_root


from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from dev.knowledge_audit.audit import KnowledgeSubstrateAudit
from dev.reports import normalize_report
from dev.reports import normalize_report
from dev.reports import (
    EngineeringReportRenderer,
    normalize_report,
)
from dev.reports import normalize_report
from dev.reports import normalize_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_CATALOG_DB,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT
        / "docs/audits/genesis_ix_a5_pack1",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--show-runtime",
        action="store_true",
    )
    args = parser.parse_args()

    if args.show_runtime:
        print(RUNTIME.to_json())

    legacy_report = KnowledgeSubstrateAudit(
        database_path=args.database,
        limit=args.limit,
    ).execute()
    report = normalize_report(
        legacy_report,
        title=(
            "Genesis IX-A5 Pack 1 — "
            "Knowledge Substrate Retrieval Audit"
        ),
        classification=(
            legacy_report.get("classification", "UNKNOWN")
            if isinstance(legacy_report, dict)
            else getattr(
                legacy_report,
                "classification",
                "UNKNOWN",
            )
        ),
    )
    report = normalize_report(
        report,
        title=(
            "Genesis IX-A5 Pack 1 — "
            "Knowledge Substrate Retrieval Audit"
        ),
        classification=(
            report.get("classification", "UNKNOWN")
            if isinstance(report, dict)
            else getattr(report, "classification", "UNKNOWN")
        ),
    )
    report = normalize_report(
        report,
        title=(
            "Genesis IX-A5 Pack 1 — "
            "Knowledge Substrate Retrieval Audit"
        ),
        classification=(
            report.get("classification", "UNKNOWN")
            if isinstance(report, dict)
            else getattr(report, "classification", "UNKNOWN")
        ),
    )
    report = normalize_report(
        report,
        title=(
            "Genesis IX-A5 Pack 1 — "
            "Knowledge Substrate Retrieval Audit"
        ),
        classification=(
            report.get("classification", "UNKNOWN")
            if isinstance(report, dict)
            else getattr(report, "classification", "UNKNOWN")
        ),
    )
    data = report.to_dict()

    output_dir = args.output_dir

    if not output_dir.is_absolute():
        output_dir = PROJECT_ROOT / output_dir

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    (output_dir / "retrieval_audit.json").write_text(
        json.dumps(
            report.to_dict(),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "retrieval_audit.md").write_text(
        EngineeringReportRenderer.render_markdown(report),
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A5 PACK 1 — KNOWLEDGE SUBSTRATE RETRIEVAL AUDIT")
    print("=" * 76)
    print("Project root   :", PROJECT_ROOT)
    print("Database       :", data["database"]["path"])
    print("Classification :", data["classification"])
    print("Known raw hits :", data["summary"]["known_raw_hits"])
    print("Known qual hits:", data["summary"]["known_qualified_hits"])
    print("FTS rows       :", data["summary"]["fts_rows"])
    print("Chunk rows     :", data["summary"]["chunk_rows"])
    print("Output         :", output_dir)
    print("=" * 76)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
