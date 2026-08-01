from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.coverage.graph.directorate_projection_public_api import (
    ConstitutionalDirectorateProjectionEngine,
    ConstitutionalDirectorateProjectionReporter,
    ConstitutionalDirectorateQueryService,
    choose_directorate,
)


def fixture(root: Path) -> Path:
    source = root / "pack3b2b1"
    source.mkdir()

    directorates = (
        ("executive", "Executive Directorate"),
        ("governance", "Governance Directorate"),
        ("knowledge", "Knowledge Directorate"),
        ("reasoning", "Reasoning Directorate"),
        ("software_engineering", "Software Engineering Directorate"),
        ("planning", "Planning Directorate"),
        ("operations", "Operations Directorate"),
        ("intelligence_acquisition", "Intelligence Acquisition Directorate"),
    )
    responsibilities = (
        ("executive", "mission_direction", "Mission direction and executive command"),
        ("governance", "constitutional_governance", "Constitutional governance and certification"),
        ("knowledge", "knowledge_stewardship", "Knowledge stewardship and catalog integrity"),
        ("reasoning", "cognitive_reasoning", "Reasoning, evidence synthesis, and inference"),
        ("software_engineering", "software_delivery", "Software architecture and delivery"),
        ("planning", "mission_planning", "Mission planning and plan integrity"),
        ("operations", "operational_execution", "Operational execution and telemetry"),
        ("intelligence_acquisition", "intelligence_acquisition", "External intelligence acquisition"),
    )

    nodes = [{
        "node_id": "organizational_unit:jarvis",
        "node_kind": "organizational_unit",
        "label": "JARVIS Executive Organization",
        "canonical_key": "jarvis",
        "attributes": {"root": True},
        "fingerprint": "organization-fp",
    }]
    edges = []

    for key, label in directorates:
        directorate_id = f"directorate:{key}"
        nodes.append({
            "node_id": directorate_id,
            "node_kind": "directorate",
            "label": label,
            "canonical_key": key,
            "attributes": {"canonical": True},
            "fingerprint": f"directorate-{key}-fp",
        })
        edges.append({
            "edge_id": f"supervises:organizational_unit:jarvis:{directorate_id}",
            "source_node_id": "organizational_unit:jarvis",
            "target_node_id": directorate_id,
            "edge_kind": "supervises",
            "attributes": {"canonical": True},
            "fingerprint": f"supervises-{key}-fp",
        })

    for directorate_key, responsibility_key, label in responsibilities:
        responsibility_id = f"responsibility:{responsibility_key}"
        directorate_id = f"directorate:{directorate_key}"
        nodes.append({
            "node_id": responsibility_id,
            "node_kind": "responsibility",
            "label": label,
            "canonical_key": responsibility_key,
            "attributes": {"canonical": True},
            "fingerprint": f"responsibility-{responsibility_key}-fp",
        })
        edges.append({
            "edge_id": f"responsible_for:{directorate_id}:{responsibility_id}",
            "source_node_id": directorate_id,
            "target_node_id": responsibility_id,
            "edge_kind": "responsible_for",
            "attributes": {"canonical": True},
            "fingerprint": f"responsible-{responsibility_key}-fp",
        })

    nodes.extend([
        {
            "node_id": "ownership_domain:core.governance",
            "node_kind": "ownership_domain",
            "label": "core/governance",
            "canonical_key": "core.governance",
            "attributes": {"repository_path": "core/governance"},
            "fingerprint": "domain-governance-fp",
        },
        {
            "node_id": "ownership_domain:tests",
            "node_kind": "ownership_domain",
            "label": "tests",
            "canonical_key": "tests",
            "attributes": {"repository_path": "tests"},
            "fingerprint": "domain-tests-fp",
        },
    ])

    payload = {
        "schema_version": "1.0.0",
        "article_intelligence_fingerprint": "article-fp",
        "graph_foundation_fingerprint": "graph-fp",
        "authority_graph_fingerprint": "authority-fp",
        "repository_projection_fingerprint": "repository-fp",
        "directorate_foundation_fingerprint": "directorate-foundation-fp",
        "nodes": nodes,
        "edges": edges,
        "integrity": {"diagnostics": [], "is_valid": True},
        "diagnostics": [],
    }
    (source / "constitutional_directorate_foundation.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    return source


class DirectorateProjectionTests(unittest.TestCase):
    def test_rule_selection(self):
        self.assertEqual(choose_directorate("core/governance/constitution"), "governance")
        self.assertEqual(choose_directorate("tests"), "software_engineering")

    def test_projection_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = fixture(Path(tmp))
            engine = ConstitutionalDirectorateProjectionEngine()
            first = engine.assess(pack3b2b1_directory=src)
            second = engine.assess(pack3b2b1_directory=src)
        self.assertEqual(
            first["directorate_projection_fingerprint"],
            second["directorate_projection_fingerprint"],
        )

    def test_ownership_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
        self.assertEqual(result["metrics"]["ownership_completeness_ratio"], 1.0)

    def test_governance_owns_governance_domain(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
            query = ConstitutionalDirectorateQueryService(result["graph"])
        self.assertEqual(
            [node.canonical_key for node in query.owned_by("governance")],
            ["core.governance"],
        )

    def test_engineering_owns_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
            query = ConstitutionalDirectorateQueryService(result["graph"])
        self.assertEqual(
            [node.canonical_key for node in query.owned_by("software_engineering")],
            ["tests"],
        )

    def test_owner_lookup(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
            query = ConstitutionalDirectorateQueryService(result["graph"])
        owner = query.owner_of_domain("ownership_domain:core.governance")
        self.assertIsNotNone(owner)
        self.assertEqual(owner.canonical_key, "governance")

    def test_unowned_domains_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
            query = ConstitutionalDirectorateQueryService(result["graph"])
        self.assertEqual(query.unowned_domains(), ())

    def test_metrics_fingerprint_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
        self.assertTrue(result["metrics"]["fingerprint"])

    def test_reporting_writes_six_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(root)
            )
            written = ConstitutionalDirectorateProjectionReporter().write(
                result,
                root / "output",
            )
        self.assertEqual(len(written), 6)

    def test_diagnostics_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = ConstitutionalDirectorateProjectionEngine().assess(
                pack3b2b1_directory=fixture(Path(tmp))
            )
        self.assertEqual(result["diagnostics"], [])


if __name__ == "__main__":
    unittest.main()
