import argparse,json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service_context import ContextAdaptiveSemanticService
p=argparse.ArgumentParser(description="Genesis X-B1.1b — Embedding Context Adaptation & Semantic Fragmentation")
p.add_argument("command",choices=("audit","prepare","embed","status","certify"))
p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
p.add_argument("--semantic-db",type=Path,default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"))
p.add_argument("--model",default="mxbai-embed-large")
p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
p.add_argument("--expected-dimensions",type=int,default=1024)
p.add_argument("--target-chars",type=int,default=2200)
p.add_argument("--overlap-chars",type=int,default=220)
p.add_argument("--limit",type=int,default=100)
p.add_argument("--batch-size",type=int,default=8)
a=p.parse_args()
s=ContextAdaptiveSemanticService(runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,
 model=a.model,ollama_url=a.ollama_url,expected_dimensions=a.expected_dimensions,
 target_chars=a.target_chars,overlap_chars=a.overlap_chars)
if a.command in ("audit","status"): out=s.audit()
elif a.command=="prepare": out=s.prepare_rejected(a.limit)
elif a.command=="embed": out=s.embed_fragments(a.limit,a.batch_size)
else: out=s.certify()
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
