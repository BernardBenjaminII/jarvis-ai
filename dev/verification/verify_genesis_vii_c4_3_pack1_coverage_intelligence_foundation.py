from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from core.governance.constitution.coverage import ConstitutionalCoverageFoundationReporter,ConstitutionalCoverageIntelligenceEngine
def check(c,l,d=""):
 print(f"[{'PASS' if c else 'FAIL'}] {l}"+(f" — {d}" if d else "")); return 0 if c else 1
def main():
 print('='*78); print('GENESIS VII-C4.3 PACK 1 — COVERAGE INTELLIGENCE FOUNDATION'); print('='*78); d=ROOT/'artifacts/audit/km0000-c4_2'; e=ConstitutionalCoverageIntelligenceEngine(); a=e.assess(audit_directory=d); b=e.assess(audit_directory=d); f=0
 for name,val in [('Repository',a.repository_fingerprint),('Extraction',a.extraction_fingerprint),('Analysis',a.analysis_fingerprint),('Ratification',a.ratification_fingerprint),('Compliance',a.compliance_fingerprint),('Certification',a.certification_fingerprint),('Repository audit',a.audit_fingerprint)]: f+=check(bool(val),f'{name} fingerprint linked',val)
 f+=check(a.coverage_fingerprint==b.coverage_fingerprint,'Coverage intelligence is deterministic',a.coverage_fingerprint); s=a.statistics; f+=check(len(a.article_metrics)==s.articles_total,'Article metric registry complete',f'records={len(a.article_metrics)}'); f+=check(s.artifacts_total>0,'Repository coverage baseline established',f'artifacts={s.artifacts_total}'); f+=check(s.articles_total>0,'Constitutional coverage baseline established',f'articles={s.articles_total}'); f+=check(s.articles_exercised+s.articles_underutilized+s.articles_unused==s.articles_total,'Every constitutional article classified'); f+=check(s.artifacts_governed+s.artifacts_ungoverned==s.artifacts_total,'Every repository artifact classified'); f+=check(not a.diagnostics,'Coverage diagnostics clear',f'diagnostics={len(a.diagnostics)}')
 out=ROOT/'artifacts/audit/km0000-c4_3-pack1'; written=ConstitutionalCoverageFoundationReporter().write(a,out); f+=check(len(written)==5,'Canonical Pack 1 artifact set',f'files={len(written)}'); invalid=[]
 for p in written:
  if p.suffix=='.json':
   try: json.loads(p.read_text())
   except Exception: invalid.append(p.name)
 f+=check(not invalid,'Pack 1 JSON artifacts valid',f'invalid={len(invalid)}'); print('-'*78); print(f'Coverage fingerprint       : {a.coverage_fingerprint}'); print(f'Articles total             : {s.articles_total}'); print(f'Articles exercised         : {s.articles_exercised}'); print(f'Articles underutilized     : {s.articles_underutilized}'); print(f'Articles unused            : {s.articles_unused}'); print(f'Article coverage ratio     : {s.article_coverage_ratio:.2%}'); print(f'Artifacts total            : {s.artifacts_total}'); print(f'Artifacts governed         : {s.artifacts_governed}'); print(f'Artifacts ungoverned       : {s.artifacts_ungoverned}'); print(f'Repository coverage ratio  : {s.repository_coverage_ratio:.2%}'); print(f'Diagnostics                : {len(a.diagnostics)}'); print('-'*78); print(f'Checks failed : {f}'); print(f"Overall status: {'EXCELLENT' if f==0 else 'FAILED'}"); print('='*78); return 0 if f==0 else 1
if __name__=='__main__': raise SystemExit(main())
