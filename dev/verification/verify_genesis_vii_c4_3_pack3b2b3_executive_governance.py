from __future__ import annotations
import json,sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from core.governance.constitution.coverage.graph.directorate_api import ExecutiveGovernanceService
from core.governance.constitution.coverage.graph.directorate_projection import ConstitutionalDirectorateProjectionEngine

def check(cond,label,detail=''):
    print(f"[{'PASS' if cond else 'FAIL'}] {label}" + (f' — {detail}' if detail else '')); return 0 if cond else 1

def main():
    print('='*78); print('GENESIS VII-C4.3 PACK 3B-2B.3 — EXECUTIVE GOVERNANCE'); print('='*78)
    source=PROJECT_ROOT/'artifacts/audit/km0000-c4_3-pack3b2b1'; projection=ConstitutionalDirectorateProjectionEngine().assess(pack3b2b1_directory=source); service=ExecutiveGovernanceService.from_projection_directory(pack3b2b1_directory=source)
    failures=0; chain=('article_intelligence_fingerprint','graph_foundation_fingerprint','authority_graph_fingerprint','repository_projection_fingerprint','directorate_foundation_fingerprint','directorate_projection_fingerprint')
    for key in chain: failures+=check(bool(projection[key]),key.replace('_',' ').title()+' preserved',str(projection[key]))
    paths=tuple(sorted(str(n.attributes.get('repository_path','')) for n in service.queries.ownership_domains()))
    unresolved=[p for p in paths if service.owner(p) is None]; failures+=check(not unresolved,'Executive ownership resolution complete',f'unresolved={len(unresolved)}')
    first=service.impact.assess(paths); second=service.impact.assess(tuple(reversed(paths))); failures+=check(first.fingerprint==second.fingerprint,'Impact analysis deterministic',first.fingerprint); failures+=check(not first.unresolved_paths,'Impact analysis resolves all canonical domains',f'unresolved={len(first.unresolved_paths)}')
    missing=[p for p in paths if not service.reviewers(p)]; failures+=check(not missing,'Reviewer determination complete',f'missing={len(missing)}')
    out=PROJECT_ROOT/'artifacts/audit/km0000-c4_3-pack3b2b3'; out.mkdir(parents=True,exist_ok=True)
    payload={'schema_version':'1.0.0','fingerprint_chain':{k:projection[k] for k in chain},'impact':first.to_dict(),'domain_summaries':[service.executive_summary(p) for p in paths]}
    jp=out/'constitutional_executive_governance.json'; jp.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n'); mp=out/'constitutional_executive_governance_summary.md'; mp.write_text(f'# Genesis VII-C4.3 Pack 3B-2B.3 — Executive Governance\n\n- Canonical domains assessed: {len(paths)}\n- Affected directorates: {len(first.affected_directorate_ids)}\n- Required reviewer directorates: {len(first.required_reviewer_directorate_ids)}\n- Unresolved paths: {len(first.unresolved_paths)}\n- Impact fingerprint: `{first.fingerprint}`\n')
    failures+=check(jp.exists() and mp.exists(),'Canonical Pack 3B-2B.3 artifacts written','files=2')
    try: json.loads(jp.read_text()); valid=True
    except json.JSONDecodeError: valid=False
    failures+=check(valid,'Pack 3B-2B.3 JSON artifact valid')
    print('-'*78); print(f'Canonical domains          : {len(paths)}'); print(f'Affected directorates      : {len(first.affected_directorate_ids)}'); print(f'Reviewer directorates      : {len(first.required_reviewer_directorate_ids)}'); print(f'Unresolved paths           : {len(first.unresolved_paths)}'); print(f'Impact fingerprint         : {first.fingerprint}'); print('-'*78); print(f'Checks failed : {failures}'); print(f"Overall status: {'EXCELLENT' if failures==0 else 'FAILED'}"); print('='*78); return 0 if failures==0 else 1
if __name__=='__main__': raise SystemExit(main())
