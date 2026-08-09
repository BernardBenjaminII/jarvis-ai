from __future__ import annotations
import argparse, json, sys
from pathlib import Path

_ENTRY_ROOT=Path(__file__).resolve().parents[1]
if str(_ENTRY_ROOT) not in sys.path:
    sys.path.insert(0,str(_ENTRY_ROOT))

from dev.runtime import bootstrap_runtime
RUNTIME=bootstrap_runtime(Path(__file__))
PROJECT_ROOT=RUNTIME.project_root

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from dev.runtime_qualification_forensics.analyzer import RuntimeQualificationForensics
from dev.runtime_qualification_forensics.render import render_markdown

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--database",type=Path,default=DEFAULT_CATALOG_DB)
    parser.add_argument("--output-dir",type=Path,default=PROJECT_ROOT/"docs/audits/genesis_ix_a5_pack3r")
    parser.add_argument("--limit",type=int,default=10)
    args=parser.parse_args()
    output=args.output_dir if args.output_dir.is_absolute() else PROJECT_ROOT/args.output_dir
    output.mkdir(parents=True,exist_ok=True)
    report=RuntimeQualificationForensics(database_path=args.database,limit=args.limit).execute()
    data=report.to_dict()
    (output/"runtime_qualification_forensics.json").write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (output/"runtime_qualification_forensics.md").write_text(render_markdown(data),encoding="utf-8")
    print("="*76)
    print("GENESIS IX-A5 PACK 3R — RUNTIME QUALIFICATION FORENSICS")
    print("="*76)
    print("Classification  :",data["classification"])
    print("Raw recall      :",f"{data['summary']['known_raw_recall']:.1%}")
    print("Qualified recall:",f"{data['summary']['known_qualified_recall']:.1%}")
    print("Top failure     :",data["summary"].get("top_failure"))
    print("Probe errors    :",data["summary"]["probe_error_count"])
    print("Output          :",output)
    print("="*76)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
