from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.coverage.graph import (
    ConstitutionalGraph,
    ConstitutionalGraphFoundationEngine,
    ConstitutionalGraphFoundationReporter,
)


def fixture(root: Path) -> Path:
    pack2 = root / "pack2"
    pack2.mkdir()
    payload = {
        "schema_version": "1.0.0",
        "article_intelligence_fingerprint": "article-intelligence",
        "article_usage": [
            {
                "article_id": "ARTICLE-1",
                "classification": "exercised",
                "reference_count": 2,
                "artifact_count": 2,
                "review_required_count": 1,
                "noncompliant_count": 0,
                "artifacts": ["RA-1", "RA-2"],
                "domains": ["governance"],
                "usage_fingerprint": "usage-1",
            },
            {
                "article_id": "ARTICLE-2",
                "classification": "unused",
                "reference_count": 0,
                "artifact_count": 0,
                "review_required_count": 0,
                "noncompliant_count": 0,
                "artifacts": [],
                "domains": [],
                "usage_fingerprint": "usage-2",
            },
        ],
    }
    (pack2 / "constitutional_article_usage.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return pack2


class GraphFoundationTests(unittest.TestCase):
    def test_deterministic_graph_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack2 = fixture(Path(tmp))
            engine = ConstitutionalGraphFoundationEngine()
            first = engine.assess(pack2_directory=pack2)
            second = engine.assess(pack2_directory=pack2)
        self.assertEqual(first.graph_fingerprint, second.graph_fingerprint)

    def test_article_intelligence_fingerprint_linked(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.article_intelligence_fingerprint, "article-intelligence")

    def test_node_registry_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertEqual(len(result.nodes), 5)

    def test_edge_registry_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertEqual(len(result.edges), 5)

    def test_integrity_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertTrue(result.integrity.is_valid)

    def test_metrics_are_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.metrics.node_count, len(result.nodes))
        self.assertEqual(result.metrics.edge_count, len(result.edges))

    def test_graph_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
            graph = ConstitutionalGraph(result.nodes, result.edges)
        self.assertIsNotNone(graph.node("article:ARTICLE-1"))

    def test_graph_reachability(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
            graph = ConstitutionalGraph(result.nodes, result.edges)
        reached = graph.reachable_from("article:ARTICLE-1")
        self.assertIn("artifact:RA-1", reached)
        self.assertIn("domain:governance", reached)

    def test_unused_article_is_isolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.metrics.isolated_node_count, 1)

    def test_reporter_writes_six_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(root)
            )
            written = ConstitutionalGraphFoundationReporter().write(
                result,
                root / "output",
            )
            for path in written:
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(written), 6)

    def test_diagnostics_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalGraphFoundationEngine().assess(
                pack2_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.diagnostics, ())


if __name__ == "__main__":
    unittest.main()
