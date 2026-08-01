from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from core.governance.constitution.ratification import (
    RATIFICATION_SCHEMA_VERSION,ConstitutionalRatificationEngine,
    ConstitutionalRatificationReporter,RatificationPolicy)

class Tests(unittest.TestCase):
    def fixture(self,root):
        root.mkdir(parents=True,exist_ok=True)
        nodes=[
          {"claim_id":"C1","source_path":"docs/constitution/executive.md","text":"Every operation must preserve evidence.","domain":"evidence","authority":"constitution","authority_rank":700,"source_hash":"a","excerpt_hash":"aa","line_start":1,"line_end":1},
          {"claim_id":"C2","source_path":"docs/decisions/ADR-1.md","text":"Every operation shall preserve evidence.","domain":"evidence","authority":"adr","authority_rank":500,"source_hash":"b","excerpt_hash":"bb","line_start":2,"line_end":2},
          {"claim_id":"C3","source_path":"docs/architecture/legacy.md","text":"Every operation must not preserve evidence.","domain":"evidence","authority":"architecture","authority_rank":400,"source_hash":"c","excerpt_hash":"cc","line_start":3,"line_end":3},
          {"claim_id":"C4","source_path":"docs/constitution/knowledge.md","text":"Knowledge must retain provenance.","domain":"knowledge","authority":"constitution","authority_rank":700,"source_hash":"d","excerpt_hash":"dd","line_start":4,"line_end":4}]
        edges=[
          {"relationship_id":"R1","source_claim_id":"C1","target_claim_id":"C2","relationship_type":"duplicates"},
          {"relationship_id":"R2","source_claim_id":"C1","target_claim_id":"C3","relationship_type":"contradicts"}]
        (root/"constitutional_analysis.json").write_text(json.dumps({"repository_fingerprint":"repo","extraction_fingerprint":"extract","analysis_fingerprint":"analysis"}))
        (root/"constitutional_graph.json").write_text(json.dumps({"nodes":nodes,"edges":edges}))
        return root
    def test_schema(self): self.assertEqual(RATIFICATION_SCHEMA_VERSION,"1.0.0")
    def test_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.fixture(Path(tmp)/"c2"); e=ConstitutionalRatificationEngine()
            self.assertEqual(e.ratify(p).ratification_fingerprint,e.ratify(p).ratification_fingerprint)
    def test_fingerprint_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=ConstitutionalRatificationEngine().ratify(self.fixture(Path(tmp)/"c2"))
            self.assertEqual((r.repository_fingerprint,r.extraction_fingerprint,r.analysis_fingerprint),("repo","extract","analysis"))
    def test_conflict_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=ConstitutionalRatificationEngine().ratify(self.fixture(Path(tmp)/"c2"))
            self.assertTrue(any(a.status=="review_required" for a in r.articles if a.domain=="evidence"))
    def test_high_authority_singleton(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=ConstitutionalRatificationEngine().ratify(self.fixture(Path(tmp)/"c2"))
            self.assertEqual([a for a in r.articles if a.domain=="knowledge"][0].status,"ratified")
    def test_traceability(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=ConstitutionalRatificationEngine().ratify(self.fixture(Path(tmp)/"c2"))
            self.assertEqual(r.statistics.unrepresented_claims,0)
    def test_policy_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=ConstitutionalRatificationEngine().ratify(self.fixture(Path(tmp)/"c2"),RatificationPolicy(minimum_supporting_claims=2,ratify_singleton_high_authority=False))
            self.assertEqual([a for a in r.articles if a.domain=="knowledge"][0].status,"rejected")
    def test_reporter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); r=ConstitutionalRatificationEngine().ratify(self.fixture(root/"c2"))
            written=ConstitutionalRatificationReporter().write(r,root/"c3")
            self.assertEqual(len(written),7)
            for p in written:
                if p.suffix==".json": json.loads(p.read_text())
if __name__=="__main__": unittest.main()
