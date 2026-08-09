from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from dev.runtime import bootstrap_runtime
R=bootstrap_runtime(Path(__file__)); PROJECT_ROOT=R.project_root
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from dev.materialization_completion_audit.audit import run

def md(data):
 c=data['checkpoint']; r=data['runtime']; rec=data['reconciliation']; f=data['failure_summary']
 lines=['# Genesis X-A1.3 — Materialization Completion & Exception Audit','',f"**Status:** **{data['status']}**",f"**Classification:** **{data['classification']}**",'', '## Completion','',f"- Registered: **{c['registered_total']:,}**",f"- Complete: **{c['complete']:,}**",f"- Failed: **{c['failed']:,}**",f"- Pending: **{c['pending']:,}**",f"- Completion: **{c['completion_rate_percent']:.4f}%**",'', '## Runtime Integrity','',f"- integrity_check: **{r['integrity_check']}**",f"- documents: **{r['counts']['runtime_documents']:,}**",f"- chunks: **{r['counts']['runtime_chunks']:,}**",f"- FTS: **{r['counts']['runtime_chunks_fts']:,}**",f"- chunk/FTS parity: **{r['chunk_fts_equal']}**",f"- reconciliation delta: **{rec['runtime_document_delta']:,}**",'', '## Failure Classes','']
 lines += [f"- `{k}`: **{v:,}**" for k,v in f['by_classification'].items()] or ['- None.']
 lines += ['', '## Dispositions','']+[f"- `{k}`: **{v:,}**" for k,v in f['by_disposition'].items()] or ['- None.']
 lines += ['', '## Checks','', '| Check | Status |','|---|---|']+[f"| `{k}` | **{'PASS' if v else 'FAIL'}** |" for k,v in data['checks'].items()]
 return '\n'.join(lines)+'\n'
def inv(data):
 lines=['# Genesis X-A1.3 — Failure Inventory','', '| Candidate | Ext | Class | Disposition | Exists | Readable | Size | Attempts | Detail | Path |','|---|---|---|---|---|---|---:|---:|---|---|']
 for x in data['failures']:
  s=x['file_state']; detail=str(x['detail']).replace('|','\\|').replace('\n',' '); path=str(x['path']).replace('|','\\|')
  lines.append(f"| `{x['candidate_id']}` | `{x['extension']}` | `{x['classification']}` | `{x['recommended_disposition']}` | {s['exists']} | {s['readable']} | {s['size_bytes'] if s['size_bytes'] is not None else '—'} | {x['attempts']} | {detail} | `{path}` |")
 return '\n'.join(lines)+'\n'
def main():
 p=argparse.ArgumentParser(); p.add_argument('--runtime-catalog',type=Path,default=DEFAULT_CATALOG_DB); p.add_argument('--checkpoint-db',type=Path,default=PROJECT_ROOT/'.runtime/materialization/genesis_x_a1_engine.sqlite'); p.add_argument('--report-dir',type=Path,default=PROJECT_ROOT/'docs/audits/genesis_x_a1_3'); p.add_argument('--preexisting-runtime-documents',type=int,default=69); a=p.parse_args()
 data=run(a.runtime_catalog,a.checkpoint_db,a.preexisting_runtime_documents); a.report_dir.mkdir(parents=True,exist_ok=True)
 (a.report_dir/'completion_audit.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n'); (a.report_dir/'completion_summary.md').write_text(md(data)); (a.report_dir/'failure_inventory.md').write_text(inv(data))
 retry=[x for x in data['failures'] if x['recommended_disposition']=='RETRY']; quarantine=[x for x in data['failures'] if x['recommended_disposition']=='QUARANTINE_OR_REPAIR']
 plan=['# Genesis X-A1.3 — Exception Disposition Plan','',f"- Retry: **{len(retry)}**",f"- Quarantine/repair: **{len(quarantine)}**",'', '## Retry','']+[f"- `{x['candidate_id']}` — `{x['path']}`" for x in retry] + ['', '## Quarantine/Repair','']+[f"- `{x['candidate_id']}` — `{x['classification']}` — `{x['path']}`" for x in quarantine]
 (a.report_dir/'exception_disposition_plan.md').write_text('\n'.join(plan)+'\n')
 print('='*76); print('GENESIS X-A1.3 — MATERIALIZATION COMPLETION & EXCEPTION AUDIT'); print('='*76); print('Status          :',data['status']); print('Classification  :',data['classification']); print('Registered      :',data['checkpoint']['registered_total']); print('Complete        :',data['checkpoint']['complete']); print('Failed          :',data['checkpoint']['failed']); print('Pending         :',data['checkpoint']['pending']); print('Completion rate :',f"{data['checkpoint']['completion_rate_percent']:.4f}%"); print('Runtime docs    :',data['runtime']['counts']['runtime_documents']); print('Runtime chunks  :',data['runtime']['counts']['runtime_chunks']); print('Runtime FTS     :',data['runtime']['counts']['runtime_chunks_fts']); print('Reconcile delta :',data['reconciliation']['runtime_document_delta']); print('Reports         :',a.report_dir); print('='*76)
 return 0 if data['status']=='EXCELLENT' else 1
if __name__=='__main__':raise SystemExit(main())
