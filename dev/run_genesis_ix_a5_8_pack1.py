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
from dev.corpus_authority import CorpusAuthorityAudit
from dev.corpus_authority.render import authority_md, pipeline_md, dropoff_md, summary_md

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_DB)
    parser.add_argument("--knowledge-root", type=Path, default=DEFAULT_KNOWLEDGE_ROOT)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "docs/audits/genesis_ix_a5_8_pack1",
    )
    args = parser.parse_args()
    output = args.output_dir if args.output_dir.is_absolute() else PROJECT_ROOT / args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    report = CorpusAuthorityAudit(
        project_root=PROJECT_ROOT,
        runtime_catalog=args.catalog,
        knowledge_root=args.knowledge_root,
    ).execute()
    data = report.to_dict()

    artifacts = {
        "corpus_authority.json": json.dumps(data, indent=2, sort_keys=True) + "\n",
        "authority_resolution.md": authority_md(data),
        "materialization_pipeline.md": pipeline_md(data),
        "corpus_dropoff.md": dropoff_md(data),
        "executive_findings.md": summary_md(data),
        "lineage_edges.json": json.dumps(data["lineage_edges"], indent=2, sort_keys=True) + "\n",
    }
    for name, content in artifacts.items():
        (output / name).write_text(content, encoding="utf-8")

    print("=" * 76)
    print("GENESIS IX-A5.8 PACK 1 — CORPUS AUTHORITY AND MATERIALIZATION TRACE")
    print("=" * 76)
    print("Classification :", data["classification"])
    print("Authority      :", data["summary"]["authoritative_path"])
    print("Catalog base   :", data["summary"]["catalog_base"])
    print("Runtime docs   :", data["summary"]["runtime_documents"])
    print("Materialized   :", f"{data['summary']['materialization_rate']:.2%}")
    print("Runtime chunks :", data["summary"]["runtime_chunks"])
    print("FTS rows       :", data["summary"]["runtime_fts_rows"])
    print("FTS coverage   :", f"{data['summary']['fts_chunk_coverage']:.2%}")
    print("Output         :", output)
    print("=" * 76)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
