from __future__ import annotations
import json, sys
from pathlib import Path
PROJECT_ROOT=Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path: sys.path.insert(0,str(PROJECT_ROOT))
from core.governance.constitution.coverage.graph.repository_public_api import *

def check(condition,label,detail=""):
    print(f"[{'PASS' if condition else 'FAIL'}] {label}" + (f" — {detail}" if detail else ""))
    return 0 if condition else 1

def main():
    print("="*78); print("GENESIS VII-C4.3 PACK 3B-2A — CONSTITUTIONAL REPOSITORY PROJECTION"); print("="*78)
    source=PROJECT_ROOT/"artifacts/audit/km0000-c4_3-pack3b1"
    e=ConstitutionalRepositoryProjectionEngine(); a=e.assess(pack3b1_directory=source); b=e.assess(pack3b1_directory=source)
    f=0
    f+=check(bool(a.article_intelligence_fingerprint),"Article intelligence fingerprint preserved",a.article_intelligence_fingerprint)
    f+=check(bool(a.graph_foundation_fingerprint),"Graph foundation fingerprint preserved",a.graph_foundation_fingerprint)
    f+=check(bool(a.authority_graph_fingerprint),"Authority graph fingerprint linked",a.authority_graph_fingerprint)
    f+=check(a.repository_projection_fingerprint==b.repository_projection_fingerprint,"Repository projection deterministic",a.repository_projection_fingerprint)
    roots=[n for n in a.nodes if n.node_kind is RepositoryNodeKind.REPOSITORY]
    f+=check(len(roots)==1,"Canonical repository root established",f"roots={len(roots)}")
    projected=[n for n in a.nodes if n.node_id.startswith("repository_artifact:")]
    f+=check(bool(projected),"Governed repository artifacts projected",f"artifacts={len(projected)}")
    f+=check(a.integrity.is_valid,"Repository projection integrity verified",f"diagnostics={len(a.integrity.diagnostics)}")
    f+=check(not a.integrity.duplicate_node_ids,"Repository node identifiers unique")
    f+=check(not a.integrity.duplicate_edge_ids,"Repository edge identifiers unique")
    f+=check(not a.integrity.dangling_edge_ids,"No dangling repository edges")
    f+=check(not a.integrity.invalid_containment_edge_ids,"Repository containment semantics valid")
    f+=check(not a.integrity.orphan_node_ids,"No orphan repository nodes")
    f+=check(a.metrics.classification_completeness_ratio==1.0,"Repository classifications complete",f"ratio={a.metrics.classification_completeness_ratio:.2%}")
    q=ConstitutionalRepositoryQueryService(ConstitutionalRepositoryProjection(a.nodes,a.edges))
    f+=check(q.packages()==q.packages() and q.modules()==q.modules(),"Repository query layer deterministic")
    f+=check(not a.diagnostics,"Repository projection diagnostics clear",f"diagnostics={len(a.diagnostics)}")
    output=PROJECT_ROOT/"artifacts/audit/km0000-c4_3-pack3b2a"
    written=ConstitutionalRepositoryProjectionReporter().write(a,output)
    expected={"constitutional_repository_projection.json","constitutional_repository_nodes.json",
              "constitutional_repository_edges.json","constitutional_repository_metrics.json",
              "constitutional_repository_integrity.json","constitutional_repository_summary.md"}
    f+=check({p.name for p in written}==expected,"Canonical Pack 3B-2A artifact set",f"files={len(written)}")
    invalid=[]
    for p in written:
        if p.suffix==".json":
            try: json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError: invalid.append(p.name)
    f+=check(not invalid,"Pack 3B-2A JSON artifacts valid",f"invalid={len(invalid)}")
    print("-"*78)
    print(f"Article intelligence fp    : {a.article_intelligence_fingerprint}")
    print(f"Graph foundation fp        : {a.graph_foundation_fingerprint}")
    print(f"Authority graph fp         : {a.authority_graph_fingerprint}")
    print(f"Repository projection fp   : {a.repository_projection_fingerprint}")
    print(f"Repository roots           : {a.metrics.repository_count}")
    print(f"Packages                   : {a.metrics.package_count}")
    print(f"Modules                    : {a.metrics.module_count}")
    print(f"Documents                  : {a.metrics.document_count}")
    print(f"Tests                      : {a.metrics.test_count}")
    print(f"Verifications              : {a.metrics.verification_count}")
    print(f"Unknown                    : {a.metrics.unknown_count}")
    print(f"Classification completeness: {a.metrics.classification_completeness_ratio:.2%}")
    print(f"Integrity valid            : {a.integrity.is_valid}")
    print(f"Diagnostics                : {len(a.diagnostics)}")
    print("-"*78); print(f"Checks failed : {f}"); print(f"Overall status: {'EXCELLENT' if f==0 else 'FAILED'}"); print("="*78)
    return 0 if f==0 else 1
if __name__=="__main__": raise SystemExit(main())
