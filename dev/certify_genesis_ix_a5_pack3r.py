from pathlib import Path
from dev.runtime_qualification_forensics.analyzer import RuntimeQualificationForensics
from dev.runtime_qualification_forensics.probes import ProbeDefinition

class Provider:
    def __init__(self): self.query=""
    def raw_search(self,query,*,database_path,limit):
        self.query=query
        return [{"source_id":"1","title":query}]
    def qualified_search(self,query,*,database_path,limit):
        self.query=query
        return []
    def last_trace(self):
        return {"threshold":0.6,"diagnostics":[{
            "source_id":"1","title":self.query,"decision":"REJECTED",
            "explanation":"lexical below threshold",
            "qualification_components":{"lexical":0.1,"phrase":0.4,"subject":0.5,"confidence":0.5,"final":0.3},
        }]}
    def last_result(self): return {}

def main():
    report=RuntimeQualificationForensics(
        database_path=Path("/tmp/cert.sqlite"),
        provider=Provider(),
        probes=(ProbeDefinition("CERT","SHA-256","known","test","cert"),),
    ).execute()
    checks={
        "probe_count":len(report.probes)==1,
        "raw_hit":report.summary["known_raw_hits"]==1,
        "qualified_zero":report.summary["known_qualified_hits"]==0,
        "reason":report.summary["top_failure"]=="LEXICAL",
        "serialization":report.to_dict()["probes"][0]["probe_id"]=="CERT",
    }
    failed=[k for k,v in checks.items() if not v]
    print("="*76)
    print("GENESIS IX-A5 PACK 3R — RUNTIME QUALIFICATION FORENSICS")
    print("="*76)
    print("Checks executed :",len(checks))
    print("Checks passed   :",len(checks)-len(failed))
    print("Checks failed   :",len(failed))
    print("Overall status  :","EXCELLENT" if not failed else "FAILED")
    print("="*76)
    return 0 if not failed else 1

if __name__=="__main__":
    raise SystemExit(main())
