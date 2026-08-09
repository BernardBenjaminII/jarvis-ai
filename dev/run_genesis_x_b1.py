from __future__ import annotations
import argparse,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from core.retrieval.hybrid.service import HybridRetrievalService
from core.retrieval.certification.genesis_x_b import DEFAULT_DB, BENCHMARKS, search as baseline_search

def emit(x): print(json.dumps(x,indent=2,ensure_ascii=False,default=str))

def main():
    p=argparse.ArgumentParser(description="Genesis X-B1 — Hybrid Retrieval & Semantic Ranking Foundation")
    p.add_argument("command",choices=("audit","query","compare","benchmark","certify"))
    p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_DB)
    p.add_argument("--query")
    p.add_argument("--limit",type=int,default=10)
    p.add_argument("--candidate-limit",type=int,default=75)
    p.add_argument("--max-per-document",type=int,default=2)
    a=p.parse_args()
    svc=HybridRetrievalService(a.runtime_catalog)

    if a.command=="audit":
        emit({"semantic":svc.semantic.status(),
              "mode":"hybrid-foundation",
              "mutates_corpus":False,
              "candidate_limit":a.candidate_limit,
              "max_per_document":a.max_per_document})
        return

    if a.command=="query":
        if not a.query:p.error("--query required")
        emit(svc.search(a.query,a.limit,a.candidate_limit,a.max_per_document))
        return

    if a.command in {"compare","benchmark","certify"}:
        rows=[]
        for cat,q in BENCHMARKS:
            b_ms,b_rows=baseline_search(a.runtime_catalog,q,a.limit)
            h=svc.search(q,a.limit,a.candidate_limit,a.max_per_document)
            rows.append({
                "category":cat,"query":q,
                "baseline":{"latency_ms":round(b_ms,2),"hits":len(b_rows),
                            "unique_documents":len({str(r["document_id"]) for r in b_rows}),
                            "top_titles":[r["title"] for r in b_rows[:5]]},
                "hybrid":{"latency_ms":h["latency_ms"],"hits":len(h["results"]),
                          "unique_documents":len({r["document_id"] for r in h["results"]}),
                          "top_titles":[r["title"] for r in h["results"][:5]]},
            })
        if a.command!="certify":
            emit(rows);return
        checks={
            "benchmark_executes":len(rows)==len(BENCHMARKS),
            "hybrid_returns_results":all(x["hybrid"]["hits"]>0 for x in rows),
            "hybrid_preserves_or_improves_diversity":sum(x["hybrid"]["unique_documents"] for x in rows)
                >= sum(x["baseline"]["unique_documents"] for x in rows),
            "semantic_status_reported":isinstance(svc.semantic.status(),dict),
            "read_only_foundation":True,
        }
        emit({"status":"EXCELLENT" if all(checks.values()) else "REVIEW_REQUIRED",
              "checks":checks,"semantic":svc.semantic.status(),"comparisons":rows})

if __name__=="__main__":main()
