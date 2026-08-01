from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.coverage.graph.authority_public_api import (
    AuthorityEdgeKind,
    AuthorityNodeKind,
    ConstitutionalAuthorityGraph,
    ConstitutionalAuthorityGraphEngine,
    ConstitutionalAuthorityGraphReporter,
    ConstitutionalAuthorityQueryService,
)


def fixture(root: Path) -> Path:
    pack3a = root / "pack3a"
    pack3a.mkdir()
    payload = {
        "schema_version": "1.0.0",
        "article_intelligence_fingerprint": "article-intelligence-fp",
        "graph_fingerprint": "graph-foundation-fp",
        "nodes": [
            {
                "node_id": "article:ARTICLE-1",
                "node_type": "article",
                "label": "ARTICLE-1",
                "attributes": {
                    "classification": "exercised",
                    "reference_count": 2,
                },
                "node_fingerprint": "n1",
            },
            {
                "node_id": "article:ARTICLE-2",
                "node_type": "article",
                "label": "ARTICLE-2",
                "attributes": {
                    "classification": "unused",
                    "reference_count": 0,
                },
                "node_fingerprint": "n2",
            },
            {
                "node_id": "artifact:RA-1",
                "node_type": "repository_artifact",
                "label": "RA-1",
                "attributes": {},
                "node_fingerprint": "n3",
            },
            {
                "node_id": "domain:governance",
                "node_type": "domain",
                "label": "governance",
                "attributes": {},
                "node_fingerprint": "n4",
            },
        ],
        "edges": [
            {
                "edge_id": "governs:ARTICLE-1:RA-1",
                "source_node_id": "article:ARTICLE-1",
                "target_node_id": "artifact:RA-1",
                "edge_type": "governs",
                "attributes": {},
                "edge_fingerprint": "e1",
            },
            {
                "edge_id": "observed:ARTICLE-1:governance",
                "source_node_id": "article:ARTICLE-1",
                "target_node_id": "domain:governance",
                "edge_type": "observed_in_domain",
                "attributes": {},
                "edge_fingerprint": "e2",
            },
        ],
    }
    (pack3a / "constitutional_graph_foundation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return pack3a


class ConstitutionalAuthorityGraphTests(unittest.TestCase):
    def test_authority_graph_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = fixture(Path(tmp))
            engine = ConstitutionalAuthorityGraphEngine()
            first = engine.assess(pack3a_directory=source)
            second = engine.assess(pack3a_directory=source)
        self.assertEqual(
            first.authority_graph_fingerprint,
            second.authority_graph_fingerprint,
        )

    def test_fingerprint_chain_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.graph_foundation_fingerprint, "graph-foundation-fp")
        self.assertEqual(
            result.article_intelligence_fingerprint,
            "article-intelligence-fp",
        )

    def test_all_articles_are_projected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        articles = [
            node for node in result.nodes
            if node.node_kind is AuthorityNodeKind.CONSTITUTIONAL_ARTICLE
        ]
        self.assertEqual(len(articles), 2)

    def test_all_authority_classes_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        classes = [
            node for node in result.nodes
            if node.node_kind is AuthorityNodeKind.AUTHORITY_CLASS
        ]
        self.assertEqual(len(classes), 5)

    def test_governs_edge_becomes_authorizes_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        authorization_edges = [
            edge for edge in result.edges
            if edge.edge_kind is AuthorityEdgeKind.AUTHORIZES
        ]
        self.assertEqual(len(authorization_edges), 1)

    def test_integrity_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        self.assertTrue(result.integrity.is_valid)

    def test_metrics_are_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.metrics.article_count, 2)
        self.assertEqual(result.metrics.exercised_article_count, 1)
        self.assertEqual(result.metrics.unexercised_article_count, 1)
        self.assertEqual(result.metrics.authority_utilization_ratio, 0.5)

    def test_query_governed_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
            service = ConstitutionalAuthorityQueryService(
                ConstitutionalAuthorityGraph(result.nodes, result.edges)
            )
        artifacts = service.governed_artifacts_for_article("ARTICLE-1")
        self.assertEqual([item.label for item in artifacts], ["RA-1"])

    def test_query_governing_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
            service = ConstitutionalAuthorityQueryService(
                ConstitutionalAuthorityGraph(result.nodes, result.edges)
            )
        articles = service.governing_articles_for_artifact("RA-1")
        self.assertEqual([item.label for item in articles], ["ARTICLE-1"])

    def test_query_by_authority_class(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
            service = ConstitutionalAuthorityQueryService(
                ConstitutionalAuthorityGraph(result.nodes, result.edges)
            )
        cold = service.articles_by_authority_class("cold")
        self.assertEqual([item.label for item in cold], ["ARTICLE-2"])

    def test_query_unexercised_articles(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
            service = ConstitutionalAuthorityQueryService(
                ConstitutionalAuthorityGraph(result.nodes, result.edges)
            )
        unused = service.unexercised_articles()
        self.assertEqual([item.label for item in unused], ["ARTICLE-2"])

    def test_reporter_writes_six_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(root)
            )
            written = ConstitutionalAuthorityGraphReporter().write(
                result,
                root / "output",
            )
            for path in written:
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(written), 6)

    def test_diagnostics_are_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalAuthorityGraphEngine().assess(
                pack3a_directory=fixture(Path(tmp))
            )
        self.assertEqual(result.diagnostics, ())


if __name__ == "__main__":
    unittest.main()
