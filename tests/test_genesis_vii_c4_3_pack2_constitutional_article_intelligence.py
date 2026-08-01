from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from core.governance.constitution.coverage import ConstitutionalArticleIntelligenceEngine, ConstitutionalArticleIntelligenceReporter, ConstitutionalArticleQueryService

def fixture(root: Path):
    p1, c42 = root/"p1", root/"c42"
    p1.mkdir(); c42.mkdir()
    (p1/"constitutional_coverage_metrics.json").write_text(json.dumps({"article_metrics":[
        {"article_id":"A-1","reference_count":3,"artifact_count":2,"classification":"exercised","compliant_count":1,"review_required_count":1,"noncompliant_count":0},
        {"article_id":"A-2","reference_count":0,"artifact_count":0,"classification":"unused","compliant_count":0,"review_required_count":0,"noncompliant_count":0}
    ]}))
    (p1/"constitutional_coverage_traceability.json").write_text(json.dumps({"coverage_fingerprint":"coverage"}))
    (c42/"constitutional_repository_inventory.json").write_text(json.dumps({"artifacts":[
        {"artifact_id":"R-1","domain":"architecture"},{"artifact_id":"R-2","domain":"governance"}
    ]}))
    (c42/"constitutional_repository_audit.json").write_text(json.dumps({"assessments":[
        {"artifact_id":"R-1","applicable_articles":["A-1"]},{"artifact_id":"R-2","applicable_articles":["A-1"]}
    ]}))
    return p1, c42

class Tests(unittest.TestCase):
    def assess(self):
        self.tmp = tempfile.TemporaryDirectory()
        p1, c42 = fixture(Path(self.tmp.name))
        return ConstitutionalArticleIntelligenceEngine().assess(pack1_directory=p1, c4_2_directory=c42)

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1,c42=fixture(Path(tmp)); e=ConstitutionalArticleIntelligenceEngine()
            self.assertEqual(e.assess(pack1_directory=p1,c4_2_directory=c42).article_intelligence_fingerprint,
                             e.assess(pack1_directory=p1,c4_2_directory=c42).article_intelligence_fingerprint)
    def test_usage_complete(self): self.assertEqual(len(self.assess().usage_registry),2)
    def test_domains(self): self.assertEqual(self.assess().usage_registry[0]["domains"],["architecture","governance"])
    def test_influence_complete(self): self.assertEqual(len(self.assess().influence_scores),2)
    def test_rankings_complete(self): self.assertEqual(len(self.assess().rankings["most_referenced"]),2)
    def test_unused(self): self.assertEqual(self.assess().rankings["never_exercised"],["A-2"])
    def test_heatmap(self): self.assertEqual(len(self.assess().heatmap["cells"]),2)
    def test_query_service(self):
        r=self.assess(); q=ConstitutionalArticleQueryService(list(r.usage_registry),list(r.influence_scores))
        self.assertEqual(q.unused_articles()[0]["article_id"],"A-2")
    def test_reporter(self):
        with tempfile.TemporaryDirectory() as tmp:
            r=self.assess(); paths=ConstitutionalArticleIntelligenceReporter().write(r,Path(tmp))
            self.assertEqual(len(paths),6)
            for p in paths:
                if p.suffix==".json": json.loads(p.read_text())
    def test_diagnostics(self): self.assertEqual(self.assess().diagnostics,())

if __name__=="__main__": unittest.main()
