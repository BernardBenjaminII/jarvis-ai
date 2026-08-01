from __future__ import annotations
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.governance.constitution.ratification import RATIFICATION_SCHEMA_VERSION,ConstitutionalRatificationEngine,ConstitutionalRatificationReporter

def check(ok,label,detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}"+(f" — {detail}" if detail else ""))
    return 0 if ok else 1

def main():
    print("="*72); print("GENESIS VII-C3 — CONSTITUTIONAL RATIFICATION ENGINE"); print("="*72)
    engine=ConstitutionalRatificationEngine(); source=ROOT/"artifacts/audit/km0000-c2"
    first,second=engine.ratify(source),engine.ratify(source); failures=0
    failures+=check(first.schema_version==RATIFICATION_SCHEMA_VERSION,"Ratification schema is supported",first.schema_version)
    failures+=check(bool(first.repository_fingerprint),"Repository fingerprint linked",first.repository_fingerprint)
    failures+=check(bool(first.extraction_fingerprint),"Extraction fingerprint linked",first.extraction_fingerprint)
    failures+=check(bool(first.analysis_fingerprint),"Analysis fingerprint linked",first.analysis_fingerprint)
    failures+=check(first.ratification_fingerprint==second.ratification_fingerprint,"Ratification is deterministic",first.ratification_fingerprint)
    aids=[a.article_id for a in first.articles]; sids=[s.section_id for s in first.sections]; tids=[t.article_id for t in first.traceability]
    failures+=check(len(aids)==len(set(aids)),"Article identifiers are unique",f"count={len(aids)}")
    failures+=check(len(sids)==len(set(sids)),"Section identifiers are unique",f"count={len(sids)}")
    failures+=check(set(aids)==set(tids),"Every article has traceability",f"articles={len(aids)}")
    failures+=check(all(a.section_id in set(sids) for a in first.articles),"Every article belongs to an existing section")
    failures+=check(first.statistics.unrepresented_claims==0,"Every C2 claim is represented",f"traced={first.statistics.traced_claims}")
    written=ConstitutionalRatificationReporter().write(first,ROOT/"artifacts/audit/km0000-c3")
    expected={"constitutional_ratification.json","constitutional_articles.json","constitutional_sections.json","constitutional_registry.json","constitutional_index.json","constitutional_traceability.json","constitutional_ratification_report.md"}
    failures+=check({p.name for p in written}==expected,"Canonical C3 artifact set",f"files={len(written)}")
    invalid=[]
    for p in written:
        if p.suffix==".json":
            try: json.loads(p.read_text())
            except json.JSONDecodeError: invalid.append(p.name)
    failures+=check(not invalid,"C3 JSON artifacts are valid",f"invalid={len(invalid)}")
    s=first.statistics
    print("-"*72)
    print(f"Repository fingerprint   : {first.repository_fingerprint}")
    print(f"Extraction fingerprint   : {first.extraction_fingerprint}")
    print(f"Analysis fingerprint     : {first.analysis_fingerprint}")
    print(f"Ratification fingerprint : {first.ratification_fingerprint}")
    print(f"Claims                   : {s.claims}")
    print(f"Clusters                 : {s.clusters}")
    print(f"Articles                 : {s.articles}")
    print(f"Ratified articles        : {s.ratified_articles}")
    print(f"Review required          : {s.review_required_articles}")
    print(f"Rejected articles        : {s.rejected_articles}")
    print(f"Sections                 : {s.sections}")
    print(f"Traced claims            : {s.traced_claims}")
    print(f"Unrepresented claims     : {s.unrepresented_claims}")
    print(f"Diagnostics              : {s.diagnostics}")
    print("-"*72); print(f"Checks failed : {failures}"); print(f"Overall status: {'EXCELLENT' if failures==0 else 'FAILED'}"); print("="*72)
    return 0 if failures==0 else 1
if __name__=="__main__": raise SystemExit(main())
