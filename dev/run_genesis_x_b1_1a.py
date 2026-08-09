import argparse,json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service_reliable import ReliableSemanticIndexService
p=argparse.ArgumentParser(description="Genesis X-B1.1a — Embedding Reliability & Failure Isolation")
p.add_argument("command",choices=("audit","embed","status","certify"))
p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
p.add_argument("--semantic-db",type=Path,default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"))
p.add_argument("--model",default="mxbai-embed-large"); p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
p.add_argument("--limit",type=int,default=100); p.add_argument("--batch-size",type=int,default=8)
p.add_argument("--expected-dimensions",type=int,default=1024); p.add_argument("--max-batch-retries",type=int,default=2)
a=p.parse_args()
s=ReliableSemanticIndexService(runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,model=a.model,
 ollama_url=a.ollama_url,expected_dimensions=a.expected_dimensions,max_batch_retries=a.max_batch_retries)
if a.command in ("audit","status"): out=s.status()
elif a.command=="embed": out=s.embed(limit=max(1,a.limit),batch_size=max(1,a.batch_size))
else: out=s.certify()
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
