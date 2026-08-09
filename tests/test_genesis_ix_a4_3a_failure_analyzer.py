from __future__ import annotations
import json, tempfile
from pathlib import Path
import unittest
from core.retrieval.failure_analysis import CertificationFailureAnalyzer

class Tests(unittest.TestCase):
    def fixture(self, root, code, query="sha256"):
        p = root / "cert.json"
        p.write_text(json.dumps({
            "schema_version":"genesis_ix_a4_3_v1","status":"FAILED",
            "checks":[{"code":code,"label":code,"status":"FAIL","detail":"fixture","expected":True,"actual":False}],
            "known_trace":{"query":query,"prompt":"JARVIS KNOWLEDGE GROUNDING:\n- No catalog evidence was retrieved.","grounding":{},"metadata":{}},
            "gap_trace":{"query":"warp","prompt":"JARVIS KNOWLEDGE GROUNDING:\nKnowledge gaps:","grounding":{},"metadata":{}},
            "runtime_snapshot":{},
        }), encoding="utf-8")
        return p

    def test_metadata_query(self):
        with tempfile.TemporaryDirectory() as d:
            report = CertificationFailureAnalyzer(self.fixture(Path(d),"KNOWN-EVIDENCE")).analyze()
            self.assertEqual(report["analyses"][0]["classification"],"DATA_QUALITY")
            self.assertFalse(report["analyses"][0]["blocking"])

    def test_gap_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            report = CertificationFailureAnalyzer(self.fixture(Path(d),"GAP-DECLARATION")).analyze()
            self.assertEqual(report["analyses"][0]["classification"],"METADATA_MISMATCH")

    def test_runtime_blocking(self):
        with tempfile.TemporaryDirectory() as d:
            report = CertificationFailureAnalyzer(self.fixture(Path(d),"RUNTIME-GROUNDING")).analyze()
            self.assertTrue(report["analyses"][0]["blocking"])

    def test_no_failures(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/"cert.json"
            p.write_text(json.dumps({"schema_version":"genesis_ix_a4_3_v1","status":"EXCELLENT","checks":[]}), encoding="utf-8")
            report = CertificationFailureAnalyzer(p).analyze()
            self.assertEqual(report["status"],"EXCELLENT")

if __name__ == "__main__":
    unittest.main()
