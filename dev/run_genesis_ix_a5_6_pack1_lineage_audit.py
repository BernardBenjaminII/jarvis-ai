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


from dev.metadata_lineage import MetadataJoinLineageAudit
from dev.metadata_lineage.render import (
    render_summary,
    render_table_profiles,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--knowledge-root",
        type=Path,
        default=Path(
            "/media/abdullah/JARVISDATA/Knowledge"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT
        / "docs/audits/genesis_ix_a5_6_pack1",
    )
    args = parser.parse_args()

    output = args.output_dir
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    report = MetadataJoinLineageAudit(
        project_root=PROJECT_ROOT,
        knowledge_root=args.knowledge_root,
    ).execute()
    data = report.to_dict()

    (output / "metadata_lineage_audit.json").write_text(
        json.dumps(
            data,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "metadata_lineage_audit.md").write_text(
        render_summary(data),
        encoding="utf-8",
    )
    (output / "table_profiles.md").write_text(
        render_table_profiles(data),
        encoding="utf-8",
    )

    print("=" * 76)
    print("GENESIS IX-A5.6 PACK 1 — METADATA JOIN AND LINEAGE AUDIT")
    print("=" * 76)
    print("Classification :", data["classification"])
    print("Databases      :", data["summary"]["database_count"])
    print("Tables         :", data["summary"]["table_count"])
    print("Join candidates:", data["summary"]["join_candidate_count"])
    print("Preferred joins:", data["summary"]["preferred_join_count"])
    print("Propagation    :", data["summary"]["propagation_path_count"])
    print("Output         :", output)
    print("=" * 76)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
