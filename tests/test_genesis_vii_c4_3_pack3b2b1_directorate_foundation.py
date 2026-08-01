from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.coverage.graph.directorate_public_api import (
    CANONICAL_DIRECTORATES,
    ConstitutionalDirectorateFoundationEngine,
    DirectorateNodeKind,
)


def fixture(root: Path) -> Path:
    source = root / "pack3b2a"
    source.mkdir()
    payload = {
        "schema_version": "1.0.0",
        "article_intelligence_fingerprint": "article-fp",
        "graph_foundation_fingerprint": "graph-fp",
        "authority_graph_fingerprint": "authority-fp",
        "repository_projection_fingerprint": "repository-fp",
        "nodes": [
            {"node_id": "repository:root", "node_kind": "repository", "path": "."},
            {"node_id": "repository_path:core", "node_kind": "package", "path": "core"},
            {"node_id": "repository_path:docs", "node_kind": "package", "path": "docs"},
        ],
        "edges": [],
    }
    (
        source / "constitutional_repository_projection.json"
    ).write_text(json.dumps(payload), encoding="utf-8")
    return source


class DirectorateFoundationTests(unittest.TestCase):
    def assess(self, root: Path):
        return ConstitutionalDirectorateFoundationEngine().assess(
            pack3b2a_directory=fixture(root)
        )

    def test_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = fixture(Path(tmp))
            engine = ConstitutionalDirectorateFoundationEngine()
            first = engine.assess(pack3b2a_directory=source)
            second = engine.assess(pack3b2a_directory=source)
        self.assertEqual(
            first.directorate_foundation_fingerprint,
            second.directorate_foundation_fingerprint,
        )

    def test_fingerprint_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertEqual(result.article_intelligence_fingerprint, "article-fp")
        self.assertEqual(result.graph_foundation_fingerprint, "graph-fp")
        self.assertEqual(result.authority_graph_fingerprint, "authority-fp")
        self.assertEqual(result.repository_projection_fingerprint, "repository-fp")

    def test_canonical_directorates_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        directorates = [
            node
            for node in result.nodes
            if node.node_kind is DirectorateNodeKind.DIRECTORATE
        ]
        self.assertEqual(len(directorates), len(CANONICAL_DIRECTORATES))

    def test_organization_root_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        roots = [
            node
            for node in result.nodes
            if node.node_kind is DirectorateNodeKind.ORGANIZATIONAL_UNIT
        ]
        self.assertEqual(len(roots), 1)

    def test_responsibilities_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        responsibilities = [
            node
            for node in result.nodes
            if node.node_kind is DirectorateNodeKind.RESPONSIBILITY
        ]
        self.assertEqual(len(responsibilities), len(CANONICAL_DIRECTORATES))

    def test_repository_ownership_domains_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        domains = [
            node
            for node in result.nodes
            if node.node_kind is DirectorateNodeKind.OWNERSHIP_DOMAIN
        ]
        self.assertEqual(len(domains), 2)

    def test_integrity_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertTrue(result.integrity.is_valid)

    def test_no_missing_directorates(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertEqual(result.integrity.missing_directorate_keys, ())

    def test_no_dangling_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertEqual(result.integrity.dangling_edge_ids, ())

    def test_no_invalid_edge_semantics(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertEqual(result.integrity.invalid_edge_ids, ())

    def test_no_orphan_responsibilities(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertEqual(result.integrity.orphan_responsibility_ids, ())

    def test_diagnostics_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.assess(Path(tmp))
        self.assertEqual(result.diagnostics, ())


if __name__ == "__main__":
    unittest.main()
