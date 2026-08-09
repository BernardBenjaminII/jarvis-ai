import argparse,json
from pathlib import Path
from core.retrieval.certification.genesis_x_b import DEFAULT_DB,audit,benchmark,certify,search
def emit(x): print(json.dumps(x,indent=2,ensure_ascii=False,default=str))
p=argparse.ArgumentParser(); p.add_argument("command",choices=["audit","benchmark","query","certify","status"]); p.add_argument("--runtime-catalog",default=str(DEFAULT_DB)); p.add_argument("--query"); p.add_argument("--limit",type=int,default=10)
a=p.parse_args(); db=Path(a.runtime_catalog)
if a.command in ("audit","status"): emit(audit(db))
elif a.command=="benchmark": emit([x.__dict__ for x in benchmark(db,a.limit)])
elif a.command=="query":
 if not a.query: p.error("--query required")
 ms,r=search(db,a.query,a.limit); emit({"query":a.query,"latency_ms":round(ms,2),"results":r})
else: emit(certify(db))
