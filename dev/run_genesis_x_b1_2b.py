import argparse,json
from pathlib import Path
from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service_scale_opt import PredictiveCorpusScaleService
p=argparse.ArgumentParser(description="Genesis X-B1.2b — Predictive Context Routing & Throughput Optimization")
p.add_argument("command",choices=("audit","execute","status","certify"))
p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
p.add_argument("--semantic-db",type=Path,default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"))
p.add_argument("--model",default="mxbai-embed-large");p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
p.add_argument("--expected-dimensions",type=int,default=1024);p.add_argument("--limit",type=int,default=1000)
p.add_argument("--canonical-batch-size",type=int,default=8);p.add_argument("--fragment-batch-size",type=int,default=8)
p.add_argument("--report-every",type=int,default=100);p.add_argument("--char-threshold",type=int,default=2250)
p.add_argument("--token-threshold",type=int,default=560);p.add_argument("--fragment-target-chars",type=int,default=1400)
p.add_argument("--fragment-overlap-chars",type=int,default=140);p.add_argument("--max-load1",type=float,default=4.0)
p.add_argument("--min-mem-gib",type=float,default=4.0);p.add_argument("--backpressure-sleep",type=float,default=1.0)
a=p.parse_args()
s=PredictiveCorpusScaleService(runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,model=a.model,
 ollama_url=a.ollama_url,expected_dimensions=a.expected_dimensions,char_threshold=a.char_threshold,
 token_threshold=a.token_threshold,fragment_target_chars=a.fragment_target_chars,
 fragment_overlap_chars=a.fragment_overlap_chars,max_load1=a.max_load1,min_mem_gib=a.min_mem_gib,
 backpressure_sleep=a.backpressure_sleep)
if a.command in ("audit","status"):out=s.status()
elif a.command=="execute":out=s.execute(limit=max(1,a.limit),canonical_batch_size=max(1,a.canonical_batch_size),
 fragment_batch_size=max(1,a.fragment_batch_size),report_every=max(1,a.report_every))
else:out=s.certify()
print(json.dumps(out,indent=2,ensure_ascii=False,default=str))
