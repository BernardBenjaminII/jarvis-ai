import argparse,json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service_context_rev2 import RecursiveContextAdaptiveService
p=argparse.ArgumentParser(description='Genesis X-B1.1b Revision 2 — Recursive Context Adaptation')
p.add_argument('command',choices=('audit','adapt','embed','status','certify'))
p.add_argument('--runtime-catalog',type=Path,default=DEFAULT_CATALOG_DB)
p.add_argument('--semantic-db',type=Path,default=Path('/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite'))
p.add_argument('--model',default='mxbai-embed-large'); p.add_argument('--ollama-url',default='http://127.0.0.1:11434')
p.add_argument('--expected-dimensions',type=int,default=1024); p.add_argument('--fallback-target-chars',type=int,default=1400)
p.add_argument('--fallback-overlap-chars',type=int,default=140); p.add_argument('--minimum-target-chars',type=int,default=700)
p.add_argument('--max-depth',type=int,default=4); p.add_argument('--limit',type=int,default=100); p.add_argument('--batch-size',type=int,default=1)
a=p.parse_args()
s=RecursiveContextAdaptiveService(runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,model=a.model,ollama_url=a.ollama_url,expected_dimensions=a.expected_dimensions,fallback_target_chars=a.fallback_target_chars,fallback_overlap_chars=a.fallback_overlap_chars,minimum_target_chars=a.minimum_target_chars,max_depth=a.max_depth)
if a.command in ('audit','status'): out=s.audit()
elif a.command=='adapt': out=s.adapt_retries(a.limit)
elif a.command=='embed': out=s.embed_leaves(a.limit,a.batch_size)
else: out=s.certify()
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
