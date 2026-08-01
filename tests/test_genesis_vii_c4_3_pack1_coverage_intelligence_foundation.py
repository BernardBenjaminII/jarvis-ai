from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from core.governance.constitution.coverage import ConstitutionalCoverageFoundationReporter,ConstitutionalCoverageIntelligenceEngine
def write_audit(d):
 d.mkdir(parents=True,exist_ok=True); arts=[{"artifact_id":"RA-1","domain":"architecture"},{"artifact_id":"RA-2","domain":"knowledge"}]; assessments=[{"artifact_id":"RA-1","overall_status":"review_required"},{"artifact_id":"RA-2","overall_status":"not_applicable"}]; usage=[{"article_id":"ARTICLE-1","reference_count":1,"compliant_count":0,"review_required_count":1,"noncompliant_count":0,"artifact_ids":["RA-1"]},{"article_id":"ARTICLE-2","reference_count":0,"compliant_count":0,"review_required_count":0,"noncompliant_count":0,"artifact_ids":[]}]
 (d/'constitutional_repository_inventory.json').write_text(json.dumps({"artifacts":arts})); (d/'constitutional_repository_audit.json').write_text(json.dumps({"repository_fingerprint":"repo","extraction_fingerprint":"extract","analysis_fingerprint":"analysis","ratification_fingerprint":"ratify","compliance_fingerprint":"comply","certification_fingerprint":"certify","audit_fingerprint":"audit","assessments":assessments})); (d/'constitutional_article_usage.json').write_text(json.dumps({"article_usage":usage}))
class T(unittest.TestCase):
 def assess(self):
  t=tempfile.TemporaryDirectory(); p=Path(t.name); write_audit(p); return t,ConstitutionalCoverageIntelligenceEngine().assess(audit_directory=p)
 def test_deterministic(self):
  with tempfile.TemporaryDirectory() as x:
   p=Path(x); write_audit(p); e=ConstitutionalCoverageIntelligenceEngine(); self.assertEqual(e.assess(audit_directory=p).coverage_fingerprint,e.assess(audit_directory=p).coverage_fingerprint)
 def test_chain(self): t,r=self.assess(); self.assertEqual(r.audit_fingerprint,'audit'); t.cleanup()
 def test_article_classes(self): t,r=self.assess(); self.assertEqual([x.classification for x in r.article_metrics],['underutilized','unused']); t.cleanup()
 def test_repo_ratio(self): t,r=self.assess(); self.assertEqual(r.statistics.repository_coverage_ratio,.5); t.cleanup()
 def test_article_ratio(self): t,r=self.assess(); self.assertEqual(r.statistics.article_coverage_ratio,.5); t.cleanup()
 def test_domains(self): t,r=self.assess(); self.assertIn('governance',{x.domain for x in r.domain_metrics}); t.cleanup()
 def test_no_diagnostics(self): t,r=self.assess(); self.assertEqual(r.diagnostics,()); t.cleanup()
 def test_reporter(self):
  with tempfile.TemporaryDirectory() as x:
   p=Path(x); a=p/'a'; o=p/'o'; write_audit(a); r=ConstitutionalCoverageIntelligenceEngine().assess(audit_directory=a); written=ConstitutionalCoverageFoundationReporter().write(r,o); self.assertEqual(len(written),5)
if __name__=='__main__': unittest.main()
