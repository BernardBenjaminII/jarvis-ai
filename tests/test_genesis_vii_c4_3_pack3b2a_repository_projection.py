import json, tempfile, unittest
from pathlib import Path
from core.governance.constitution.coverage.graph.repository_public_api import *

def fixture(root: Path) -> Path:
    d = root/"pack3b1"; d.mkdir()
    payload = {"schema_version":"1.0.0","article_intelligence_fingerprint":"article-intelligence-fp",
    "graph_foundation_fingerprint":"graph-foundation-fp","authority_graph_fingerprint":"authority-graph-fp",
    "nodes":[
      {"node_id":"artifact:module","node_kind":"governed_artifact","label":"core/reasoning/engine.py","attributes":{"path":"core/reasoning/engine.py"}},
      {"node_id":"artifact:test","node_kind":"governed_artifact","label":"tests/test_engine.py","attributes":{"path":"tests/test_engine.py"}},
      {"node_id":"artifact:doc","node_kind":"governed_artifact","label":"docs/architecture/reasoning.md","attributes":{"path":"docs/architecture/reasoning.md"}},
      {"node_id":"artifact:verify","node_kind":"governed_artifact","label":"dev/verification/verify_reasoning.py","attributes":{"path":"dev/verification/verify_reasoning.py"}}],
    "edges":[]}
    (d/"constitutional_authority_graph.json").write_text(json.dumps(payload), encoding="utf-8")
    return d

class RepositoryProjectionTests(unittest.TestCase):
    def assess(self, root): return ConstitutionalRepositoryProjectionEngine().assess(pack3b1_directory=fixture(root))
    def test_classifier(self):
        self.assertIs(classify_repository_path("core/reasoning/engine.py"), RepositoryNodeKind.MODULE)
        self.assertIs(classify_repository_path("tests/test_engine.py"), RepositoryNodeKind.TEST)
        self.assertIs(classify_repository_path("docs/design.md"), RepositoryNodeKind.DOCUMENT)
    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            src=fixture(Path(t)); e=ConstitutionalRepositoryProjectionEngine()
            a=e.assess(pack3b1_directory=src); b=e.assess(pack3b1_directory=src)
            self.assertEqual(a.repository_projection_fingerprint,b.repository_projection_fingerprint)
    def test_chain(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.assess(Path(t))
            self.assertEqual((r.authority_graph_fingerprint,r.graph_foundation_fingerprint,r.article_intelligence_fingerprint),
                             ("authority-graph-fp","graph-foundation-fp","article-intelligence-fp"))
    def test_root(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.assess(Path(t)); self.assertEqual(sum(n.node_kind is RepositoryNodeKind.REPOSITORY for n in r.nodes),1)
    def test_artifacts(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.assess(Path(t)); self.assertEqual(sum(n.node_id.startswith("repository_artifact:") for n in r.nodes),4)
    def test_packages(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.assess(Path(t)); self.assertTrue(any(n.node_kind is RepositoryNodeKind.PACKAGE for n in r.nodes))
    def test_integrity(self):
        with tempfile.TemporaryDirectory() as t: self.assertTrue(self.assess(Path(t)).integrity.is_valid)
    def test_complete(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.assess(Path(t)); self.assertEqual(r.metrics.unknown_count,0); self.assertEqual(r.metrics.classification_completeness_ratio,1.0)
    def test_queries(self):
        with tempfile.TemporaryDirectory() as t:
            r=self.assess(Path(t)); q=ConstitutionalRepositoryQueryService(ConstitutionalRepositoryProjection(r.nodes,r.edges))
            self.assertEqual(len(q.modules()),1); self.assertEqual(len(q.tests()),1); self.assertGreaterEqual(len(q.descendants_of("repository:root")),4)
    def test_reporter(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); r=self.assess(root); written=ConstitutionalRepositoryProjectionReporter().write(r,root/"out")
            self.assertEqual(len(written),6)
            for p in written:
                if p.suffix==".json": json.loads(p.read_text())
    def test_diagnostics(self):
        with tempfile.TemporaryDirectory() as t: self.assertEqual(self.assess(Path(t)).diagnostics,())
if __name__=="__main__": unittest.main()
