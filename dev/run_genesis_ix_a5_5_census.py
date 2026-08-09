from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
RUNTIME=bootstrap_runtime(Path(__file__)); PROJECT_ROOT=RUNTIME.project_root
from dev.knowledge_census import KnowledgeCensus
from dev.knowledge_census import render
def main():
 p=argparse.ArgumentParser(); p.add_argument('--knowledge-root',type=Path,default=Path('/media/abdullah/JARVISDATA/Knowledge')); p.add_argument('--output-dir',type=Path,default=PROJECT_ROOT/'docs/audits/genesis_ix_a5_5'); a=p.parse_args(); out=a.output_dir if a.output_dir.is_absolute() else PROJECT_ROOT/a.output_dir; out.mkdir(parents=True,exist_ok=True)
 d=KnowledgeCensus(project_root=PROJECT_ROOT,knowledge_root=a.knowledge_root).execute().to_dict(); files={'census.json':json.dumps(d,indent=2,sort_keys=True)+'\n','database_inventory.md':render.database_inventory(d),'schema_inventory.md':render.schema_inventory(d),'metadata_inventory.md':render.metadata_inventory(d),'retrieval_inventory.md':render.retrieval_inventory(d),'executive_compatibility.md':render.executive_compatibility(d),'reconstruction_recommendations.md':render.recommendations(d)}
 for n,c in files.items():(out/n).write_text(c,encoding='utf-8')
 print('='*76); print('GENESIS IX-A5.5 — KNOWLEDGE CENSUS'); print('='*76); print('Classification :',d['classification']); print('Databases      :',d['summary']['database_count']); print('Tables         :',d['summary']['table_count']); print('FTS tables     :',d['summary']['fts_table_count']); print('Map existing   :',d['summary']['mappable_requirements']); print('Reconstruct    :',d['summary']['missing_requirements']); print('Output         :',out); print('='*76); return 0
if __name__=='__main__': raise SystemExit(main())
