from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from core.governance.constitution.coverage import ConstitutionalArticleIntelligenceEngine, ConstitutionalArticleIntelligenceReporter, ConstitutionalArticleQueryService

def check(ok,label,detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return 0 if ok else 1

def main():
    print("="*78); print("GENESIS VII-C4.3 PACK 2 — CONSTITUTIONAL ARTICLE INTELLIGENCE"); print("="*78)
    p1=ROOT/"artifacts/audit/km0000-c4_3-pack1"; c42=ROOT/"artifacts/audit/km0000-c4_2"
    e=ConstitutionalArticleIntelligenceEngine()
    a=e.assess(pack1_directory=p1,c4_2_directory=c42)
    b=e.assess(pack1_directory=p1,c4_2_directory=c42)
    f=0
    f+=check(bool(a.coverage_fingerprint),"Coverage fingerprint linked",a.coverage_fingerprint)
    f+=check(a.article_intelligence_fingerprint==b.article_intelligence_fingerprint,"Article intelligence deterministic",a.article_intelligence_fingerprint)
    f+=check(len(a.usage_registry)>0,"Article usage registry complete",f"records={len(a.usage_registry)}")
    f+=check(len(a.influence_scores)==len(a.usage_registry),"Influence score registry complete")
    f+=check(len(a.rankings["most_referenced"])==len(a.usage_registry),"Every article ranked")
    f+=check(len(a.heatmap["cells"])==len(a.usage_registry),"Article heatmap complete")
    f+=check(sum(a.authority_distribution["classification_distribution"].values())==len(a.usage_registry),"Authority distribution complete")
    q=ConstitutionalArticleQueryService(list(a.usage_registry),list(a.influence_scores))
    f+=check(len(q.unused_articles())==len(a.rankings["never_exercised"]),"Executive query layer deterministic")
    f+=check(not a.diagnostics,"Article intelligence diagnostics clear",f"diagnostics={len(a.diagnostics)}")
    out=ROOT/"artifacts/audit/km0000-c4_3-pack2"
    written=ConstitutionalArticleIntelligenceReporter().write(a,out)
    f+=check(len(written)==6,"Canonical Pack 2 artifact set",f"files={len(written)}")
    bad=[]
    for p in written:
        if p.suffix==".json":
            try: json.loads(p.read_text())
            except json.JSONDecodeError: bad.append(p.name)
    f+=check(not bad,"Pack 2 JSON artifacts valid",f"invalid={len(bad)}")
    print("-"*78)
    print(f"Coverage fingerprint       : {a.coverage_fingerprint}")
    print(f"Article intelligence fp    : {a.article_intelligence_fingerprint}")
    print(f"Articles analyzed          : {len(a.usage_registry)}")
    print(f"Critical hotspots          : {a.heatmap['critical_count']}")
    print(f"Review hotspots            : {a.heatmap['review_count']}")
    print(f"Active articles            : {a.heatmap['active_count']}")
    print(f"Cold articles              : {a.heatmap['cold_count']}")
    print(f"Diagnostics                : {len(a.diagnostics)}")
    print("-"*78); print(f"Checks failed : {f}"); print(f"Overall status: {'EXCELLENT' if f==0 else 'FAILED'}"); print("="*78)
    return 0 if f==0 else 1
if __name__=="__main__": raise SystemExit(main())
