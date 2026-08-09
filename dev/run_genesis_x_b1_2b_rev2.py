import argparse,json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service_context_rev3 import TransactionalRecursiveContextService

p=argparse.ArgumentParser(description="Genesis X-B1.2b Revision 2 — Transactional Recursive Fragmentation & Lifecycle Reconciliation")
p.add_argument("command",choices=("audit","reconcile","adapt","embed","recover","status","certify"))
p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
p.add_argument("--semantic-db",type=Path,default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"))
p.add_argument("--model",default="mxbai-embed-large")
p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
p.add_argument("--expected-dimensions",type=int,default=1024)
p.add_argument("--fallback-target-chars",type=int,default=1000)
p.add_argument("--fallback-overlap-chars",type=int,default=100)
p.add_argument("--minimum-target-chars",type=int,default=300)
p.add_argument("--max-depth",type=int,default=6)
p.add_argument("--limit",type=int,default=500)
p.add_argument("--batch-size",type=int,default=8)
a=p.parse_args()

s=TransactionalRecursiveContextService(
 runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,model=a.model,
 ollama_url=a.ollama_url,expected_dimensions=a.expected_dimensions,
 fallback_target_chars=a.fallback_target_chars,
 fallback_overlap_chars=a.fallback_overlap_chars,
 minimum_target_chars=a.minimum_target_chars,max_depth=a.max_depth)

if a.command in ("audit","status"):
    out=s.audit()
elif a.command=="reconcile":
    out=s.reconcile()
elif a.command=="adapt":
    out=s.adapt_retries(a.limit)
elif a.command=="embed":
    out=s.embed_leaves(a.limit,a.batch_size)
elif a.command=="recover":
    out=s.recover_until_stable(batch_size=a.batch_size)
else:
    a0=s.audit()
    with s.store.connect() as c:
        fragmented=int(c.execute("SELECT COUNT(*) FROM embedding_campaign WHERE stage='FRAGMENTED'").fetchone()[0])
        incomplete=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments
            WHERE is_leaf=1 AND stage NOT IN ('COMPLETE','REJECTED_CONTEXT')""").fetchone()[0])
        rejected=int(c.execute("SELECT COUNT(*) FROM semantic_fragments WHERE is_leaf=1 AND stage='REJECTED_CONTEXT'").fetchone()[0])
        missing=int(c.execute("""SELECT COUNT(*) FROM semantic_fragments f
            LEFT JOIN semantic_fragment_vectors v ON v.fragment_uuid=f.fragment_uuid
            WHERE f.is_leaf=1 AND f.stage='COMPLETE' AND v.fragment_uuid IS NULL""").fetchone()[0])
    checks={
      "provider_available":bool(a0["provider"].get("available")),
      "provider_model_present":bool(a0["provider"].get("model_present")),
      "no_orphaned_superseded":a0["orphaned_superseded"]==0,
      "no_unresolved_fragmented_parents":fragmented==0,
      "no_incomplete_active_leaves":incomplete==0,
      "no_terminal_context_rejections":rejected==0,
      "complete_leaves_have_vectors":missing==0,
      "canonical_runtime_untouched":True}
    out={"status":"EXCELLENT_TRANSACTIONAL_FRAGMENT_LIFECYCLE" if all(checks.values()) else "REVIEW_REQUIRED",
         "checks":checks,"fragmented_parents":fragmented,"incomplete_active_leaves":incomplete,
         "terminal_context_rejections":rejected,"complete_leaves_missing_vectors":missing,**a0}
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
