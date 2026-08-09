from __future__ import annotations
import argparse,json,sys
from pathlib import Path
def root():
 c=Path(__file__).resolve()
 for p in (c.parent,*c.parents):
  if all((p/x).is_dir() for x in ('core','dev','docs')):
   if str(p) not in sys.path:sys.path.insert(0,str(p))
   return p
 raise RuntimeError('Unable to locate JARVIS root.')
ROOT=root()
from core.certification.runtime import CertificationRuntime
from core.retrieval.call_graph import ExecutiveRuntimeCallGraphReconstructor

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=ROOT); ap.add_argument('--output-dir',type=Path,default=Path('docs/audits/genesis_ix_a4_3c')); a=ap.parse_args()
 rt=CertificationRuntime(start=a.root).bootstrap(); b=rt.certify(); data=ExecutiveRuntimeCallGraphReconstructor(Path(b.repository_root)).reconstruct(); out=a.output_dir if a.output_dir.is_absolute() else Path(b.repository_root)/a.output_dir; out.mkdir(parents=True,exist_ok=True)
 (out/'runtime_call_graph.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 def table(items):
  lines=['| Owner | Method | Public | Signature | Source |','|---|---|---|---|---|']
  for x in items:lines.append(f"| `{x['owner']}` | `{x['attribute']}` | {x['public']} | `{x['signature']}` | `{x['source_file']}:{x['source_line']}` |")
  return '\n'.join(lines)
 (out/'runtime_callable_surface.md').write_text('# Executive Runtime Callable Surface\n\n'+table(data['callables'])+'\n',encoding='utf-8')
 (out/'executive_director_inspection.md').write_text('# Executive Director Inspection\n\n'+table(data['director_methods'])+'\n\n```json\n'+json.dumps(data['director_hook'],indent=2,sort_keys=True)+'\n```\n',encoding='utf-8')
 (out/'orchestrator_flow.json').write_text(json.dumps(data['orchestrator_flow'],indent=2,sort_keys=True)+'\n',encoding='utf-8')
 edges=['# Executive Runtime Call Graph','','| Source | Target | Relation | Evidence |','|---|---|---|---|']+[f"| `{e['source']}` | `{e['target']}` | {e['relation']} | `{e['evidence']}` |" for e in data['edges']]
 (out/'runtime_call_graph.md').write_text('\n'.join(edges)+'\n',encoding='utf-8')
 c=data['ix_a4_3b_repair_contract']; (out/'ix_a4_3b_hook_repair_contract.md').write_text(f"# IX-A4.3B Hook Repair Contract\n\n**Action:** `{c['action']}`\n\n{c['instructions']}\n",encoding='utf-8')
 v=data['verdict']; h=data['director_hook']; (out/'reconstruction_summary.md').write_text(f"# Genesis IX-A4.3C — Executive Runtime Call Graph Reconstruction\n\n**Classification:** **{v['classification']}**\n\n{v['reason']}\n\n- Director hook: `{h.get('method')}`\n- Repair action: `{c['action']}`\n",encoding='utf-8')
 print('='*76); print('GENESIS IX-A4.3C — EXECUTIVE RUNTIME CALL GRAPH RECONSTRUCTION'); print('='*76); print('Callables found  :',len(data['callables'])); print('Edges found      :',len(data['edges'])); print('Director methods :',len(data['director_methods'])); print('Director hook    :',h.get('method')); print('Classification   :',v['classification']); print('Output           :',out); print('='*76); return 0
if __name__=='__main__':raise SystemExit(main())
