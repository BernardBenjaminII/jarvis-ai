import unittest
from pathlib import Path
from dev.runtime_qualification_forensics.analyzer import RuntimeQualificationForensics
from dev.runtime_qualification_forensics.extract import candidate_record
from dev.runtime_qualification_forensics.probes import ProbeDefinition, canonical_runtime_probes

class FakeProvider:
    def __init__(self): self.query=""
    def raw_search(self,query,*,database_path,limit):
        self.query=query
        return [] if "Warp Core" in query else [{"source_id":"raw-1","title":query}]
    def qualified_search(self,query,*,database_path,limit):
        self.query=query
        return [{"source_id":"q-1","title":"SQLite"}] if query=="SQLite" else []
    def last_trace(self):
        if self.query=="SQLite":
            return {"threshold":0.6,"diagnostics":[{
                "source_id":"q-1","title":"SQLite","decision":"ACCEPTED",
                "qualification_components":{"lexical":0.9,"phrase":0.8,"subject":0.8,"confidence":0.8,"final":0.82},
            }]}
        return {"threshold":0.6,"diagnostics":[{
            "source_id":"r-1","title":self.query,"decision":"REJECTED",
            "explanation":"lexical below threshold",
            "qualification_components":{"lexical":0.1,"phrase":0.5,"subject":0.5,"confidence":0.5,"final":0.3},
        }]}
    def last_result(self): return None

class Tests(unittest.TestCase):
    def test_self_contained_probes(self):
        self.assertGreaterEqual(len(canonical_runtime_probes()),8)

    def test_runtime_analysis(self):
        probes=(
            ProbeDefinition("KNOWN-SQLITE","SQLite","known","test","test"),
            ProbeDefinition("KNOWN-SHA","SHA-256","known","test","test"),
            ProbeDefinition("GAP","Quantum Banana Warp Core Mk XII","unknown","test","test"),
        )
        report=RuntimeQualificationForensics(
            database_path=Path("/tmp/fake.sqlite"),
            provider=FakeProvider(),
            probes=probes,
        ).execute()
        self.assertEqual(report.summary["known_raw_hits"],2)
        self.assertEqual(report.summary["known_qualified_hits"],1)
        self.assertEqual(report.summary["top_failure"],"LEXICAL")

    def test_candidate_margin(self):
        record=candidate_record(
            {"source_id":"c1","decision":"REJECTED",
             "qualification_components":{"lexical":0.3,"final":0.4}},
            raw_rank=1,threshold=0.6,
        )
        self.assertAlmostEqual(record.margin,-0.2)

    def test_sparse_trace_fallback(self):
        class Sparse(FakeProvider):
            def last_trace(self): return {}
            def last_result(self): return {}
        report=RuntimeQualificationForensics(
            database_path=Path("/tmp/fake.sqlite"),
            provider=Sparse(),
            probes=(ProbeDefinition("KNOWN","SQLite","known","test","test"),),
        ).execute()
        self.assertEqual(report.probes[0].raw_count,1)
        self.assertGreaterEqual(len(report.probes[0].candidates),1)

if __name__=="__main__":
    unittest.main()
