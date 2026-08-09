import argparse,json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service_scale_rev2 import CorpusScaleSemanticServiceRev2

p=argparse.ArgumentParser(description="Genesis X-B1.2a — Production Context Routing & Campaign Recovery")
p.add_argument("command",choices=("audit","recover","execute","status","certify"))
p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
p.add_argument("--semantic-db",type=Path,default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"))
p.add_argument("--model",default="mxbai-embed-large")
p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
p.add_argument("--expected-dimensions",type=int,default=1024)
p.add_argument("--limit",type=int,default=1000)
p.add_argument("--batch-size",type=int,default=8)
p.add_argument("--report-every",type=int,default=100)
p.add_argument("--max-load1",type=float,default=4.0)
p.add_argument("--min-mem-gib",type=float,default=4.0)
p.add_argument("--backpressure-sleep",type=float,default=1.0)
a=p.parse_args()

s=CorpusScaleSemanticServiceRev2(
 runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,model=a.model,
 ollama_url=a.ollama_url,expected_dimensions=a.expected_dimensions,
 max_load1=a.max_load1,min_mem_gib=a.min_mem_gib,
 backpressure_sleep=a.backpressure_sleep)

if a.command in ("audit","status"):
    out=s.status()
elif a.command=="recover":
    out=s.recover_existing_context_rejections(a.limit)
elif a.command=="execute":
    out=s.execute(limit=max(1,a.limit),batch_size=max(1,a.batch_size),
                  report_every=max(1,a.report_every))
else:
    out=s.certify()

print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
