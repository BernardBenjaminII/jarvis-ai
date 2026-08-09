from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


_ENTRY_ROOT = Path(__file__).resolve().parents[1]
if str(_ENTRY_ROOT) not in sys.path:
    sys.path.insert(0, str(_ENTRY_ROOT))


from dev.runtime import bootstrap_runtime


RUNTIME = bootstrap_runtime(Path(__file__))
PROJECT_ROOT = RUNTIME.project_root


from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from dev.subject_trace import SubjectQualificationTrace
from dev.subject_trace.render import render_markdown


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
        / "docs/audits/genesis_ix_a5_pack4",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )
    args = parser.parse_args()

    output = args.output_dir
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    report = SubjectQualificationTrace(
        database_path=args.database,
        limit=args.limit,
    ).execute()
    data = report.to_dict()

    (output / "subject_trace.json").write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "subject_trace.md").write_text(
        render_markdown(data),
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A5 PACK 4 — SUBJECT QUALIFICATION TRACE")
    print("=" * 76)
    print("Classification :", data["classification"])
    print("Candidates     :", data["summary"]["candidate_count"])
    print("Missing subject:", data["summary"]["missing_subject_metadata"])
    print("Taxonomy mismatch:", data["summary"]["taxonomy_mismatches"])
    print("Top diagnosis  :", data["summary"].get("top_diagnosis"))
    print("Output         :", output)
    print("=" * 76)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
