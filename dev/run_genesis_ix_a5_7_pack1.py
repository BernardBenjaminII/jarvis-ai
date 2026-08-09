from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
RUNTIME=bootstrap_runtime(Path(__file__))
PROJECT_ROOT=RUNTIME.project_root
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB, DEFAULT_KNOWLEDGE_ROOT
from dev.intelligence import CorpusIntelligenceFramework
from dev.intelligence.render import corpus_md,databases_md,tables_md,runtime_md,relationships_md,candidates_md

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,action="append",dest="roots")
    p.add_argument("--output-dir",type=Path,default=PROJECT_ROOT/"docs/audits/genesis_ix_a5_7_pack1")
    a=p.parse_args()
    roots=tuple(a.roots or (PROJECT_ROOT,PROJECT_ROOT/".runtime",Path(DEFAULT_CATALOG_DB).parent,Path(DEFAULT_KNOWLEDGE_ROOT)))
    output=a.output_dir if a.output_dir.is_absolute() else PROJECT_ROOT/a.output_dir
    output.mkdir(parents=True,exist_ok=True)
    d=CorpusIntelligenceFramework(roots=roots).execute().to_dict()
    artifacts={
        "corpus_inventory.json":json.dumps(d,indent=2,sort_keys=True)+"\n",
        "database_candidates.md":candidates_md(d),
        "corpus_inventory.md":corpus_md(d),
        "database_inventory.md":databases_md(d),
        "table_inventory.md":tables_md(d),
        "runtime_inventory.md":runtime_md(d),
        "corpus_relationships.md":relationships_md(d),
        "relationship_graph.json":json.dumps(d["relationships"],indent=2,sort_keys=True)+"\n",
    }
    for name,text in artifacts.items(): (output/name).write_text(text,encoding="utf-8")
    print("="*76)
    print("GENESIS IX-A5.7 PACK 1 — CORPUS INTELLIGENCE FRAMEWORK")
    print("="*76)
    print("Classification :",d["classification"])
    print("Candidates     :",d["summary"]["candidate_count"])
    print("Databases      :",d["summary"]["verified_database_count"])
    print("Corpora        :",d["summary"]["table_count"])
    print("Searchable     :",d["summary"]["searchable_corpus_count"])
    print("Runtime        :",d["summary"]["runtime_corpus_count"])
    print("FTS            :",d["summary"]["fts_corpus_count"])
    print("Output         :",output)
    print("="*76)
    return 0

if __name__=="__main__": raise SystemExit(main())
