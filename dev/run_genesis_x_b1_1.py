from __future__ import annotations
import argparse,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))

from core.knowledge_catalog.config import DEFAULT_CATALOG_DB
from core.retrieval.semantic_index.service import SemanticIndexService

def emit(x):print(json.dumps(x,indent=2,ensure_ascii=False,default=str))

def main():
    p=argparse.ArgumentParser(description="Genesis X-B1.1 — Semantic Corpus Index & Chunk Identity Bridge")
    p.add_argument("command",choices=("audit","prepare","embed","status","query","certify"))
    p.add_argument("--runtime-catalog",type=Path,default=DEFAULT_CATALOG_DB)
    p.add_argument("--semantic-db",type=Path,default=Path("/media/abdullah/JARVIS_RUNTIME_L/knowledge/semantic_index.sqlite"))
    p.add_argument("--provider",default="ollama")
    p.add_argument("--model",default="mxbai-embed-large")
    p.add_argument("--ollama-url",default="http://127.0.0.1:11434")
    p.add_argument("--limit",type=int,default=100)
    p.add_argument("--batch-size",type=int,default=16)
    p.add_argument("--query")
    p.add_argument("--scan-limit",type=int)
    a=p.parse_args()
    s=SemanticIndexService(runtime_catalog=a.runtime_catalog,semantic_db=a.semantic_db,
        provider_name=a.provider,model=a.model,ollama_url=a.ollama_url)

    if a.command in ("audit","status"):emit(s.audit());return
    if a.command=="prepare":emit(s.prepare_bridge());return
    if a.command=="embed":emit(s.embed(limit=max(1,a.limit),batch_size=max(1,a.batch_size)));return
    if a.command=="query":
        if not a.query:p.error("--query required")
        emit({"query":a.query,"results":s.semantic_search(a.query,limit=a.limit,scan_limit=a.scan_limit)});return
    emit(s.certify())

if __name__=="__main__":main()
