from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dev.runtime import bootstrap_runtime
RUNTIME = bootstrap_runtime(Path(__file__))
PROJECT_ROOT = RUNTIME.project_root

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB, DEFAULT_KNOWLEDGE_ROOT
from dev.materializer_eligibility import MaterializerEligibilityAudit
from dev.materializer_eligibility.render import (
    summary_md, implementation_md, authority_md, dispositions_md
)

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--runtime-catalog", type=Path, default=DEFAULT_CATALOG_DB)
    p.add_argument(
        "--inventory-catalog",
        type=Path,
        default=Path(DEFAULT_KNOWLEDGE_ROOT) / ".jarvis/catalog.sqlite",
    )
    p.add_argument("--knowledge-root", type=Path, default=DEFAULT_KNOWLEDGE_ROOT)
    p.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "docs/audits/genesis_ix_a5_8_pack2",
    )
    a = p.parse_args()

    output = a.output_dir if a.output_dir.is_absolute() else PROJECT_ROOT / a.output_dir
    output.mkdir(parents=True, exist_ok=True)

    report = MaterializerEligibilityAudit(
        project_root=PROJECT_ROOT,
        runtime_catalog=a.runtime_catalog,
        inventory_catalog=a.inventory_catalog,
        knowledge_root=a.knowledge_root,
    ).execute()
    data = report.to_dict()

    artifacts = {
        "materializer_eligibility.json": json.dumps(data, indent=2, sort_keys=True) + "\n",
        "eligibility_summary.md": summary_md(data),
        "materializer_implementation.md": implementation_md(data),
        "authority_map.md": authority_md(data),
        "candidate_dispositions.md": dispositions_md(data),
    }
    for name, content in artifacts.items():
        (output / name).write_text(content, encoding="utf-8")

    print("=" * 76)
    print("GENESIS IX-A5.8 PACK 2 — MATERIALIZER ELIGIBILITY AUDIT")
    print("=" * 76)
    print("Classification :", data["classification"])
    print("Candidates     :", data["summary"]["candidate_count"])
    print("Materialized   :", data["summary"]["already_materialized"])
    print("Eligible gap   :", data["summary"]["eligible_not_selected"])
    print("Selection rate :", f"{data['summary']['selection_rate_among_eligible']:.2%}")
    print("Missing source :", data["summary"]["missing_source_count"])
    print("Unsupported    :", data["summary"]["unsupported_count"])
    print("Output         :", output)
    print("=" * 76)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
