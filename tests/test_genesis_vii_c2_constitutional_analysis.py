from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.analysis import (
    ANALYSIS_SCHEMA_VERSION,
    ConstitutionalAnalysisEngine,
    ConstitutionalAnalysisReporter,
)


class ConstitutionalAnalysisTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        claims = [
            {
                "claim_id": "CLAIM-1",
                "source_path": "docs/constitution/executive.md",
                "text": "Every operation must preserve evidence.",
                "modality": "must",
                "domain": "evidence",
                "line_start": 10,
                "line_end": 10,
                "repository_id": "REP-1",
                "source_hash": "a",
                "excerpt_hash": "aa",
            },
            {
                "claim_id": "CLAIM-2",
                "source_path": "docs/decisions/ADR-0001.md",
                "text": "Every operation shall preserve evidence.",
                "modality": "shall",
                "domain": "evidence",
                "line_start": 20,
                "line_end": 20,
                "repository_id": "REP-2",
                "source_hash": "b",
                "excerpt_hash": "bb",
            },
            {
                "claim_id": "CLAIM-3",
                "source_path": "docs/architecture/legacy.md",
                "text": "Every operation must not preserve evidence.",
                "modality": "must_not",
                "domain": "evidence",
                "line_start": 30,
                "line_end": 30,
                "repository_id": "REP-3",
                "source_hash": "c",
                "excerpt_hash": "cc",
            },
        ]
        (root / "constitutional_extraction.json").write_text(
            json.dumps({
                "repository_fingerprint": "repo-fp",
                "extraction_fingerprint": "extract-fp",
            }),
            encoding="utf-8",
        )
        (root / "constitutional_claims.json").write_text(
            json.dumps({"claims": claims}),
            encoding="utf-8",
        )
        return root

    def test_schema(self):
        self.assertEqual(ANALYSIS_SCHEMA_VERSION, "1.0.0")

    def test_determinism(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self._fixture(Path(tmp) / "c1")
            engine = ConstitutionalAnalysisEngine()
            first = engine.analyze(source)
            second = engine.analyze(source)
            self.assertEqual(first.analysis_fingerprint, second.analysis_fingerprint)
            self.assertEqual(first.relationships, second.relationships)

    def test_repository_and_extraction_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            analysis = ConstitutionalAnalysisEngine().analyze(self._fixture(Path(tmp) / "c1"))
            self.assertEqual(analysis.repository_fingerprint, "repo-fp")
            self.assertEqual(analysis.extraction_fingerprint, "extract-fp")

    def test_claim_ordering(self):
        with tempfile.TemporaryDirectory() as tmp:
            analysis = ConstitutionalAnalysisEngine().analyze(self._fixture(Path(tmp) / "c1"))
            keys = [(c.source_path, c.line_start, c.claim_id) for c in analysis.claims]
            self.assertEqual(keys, sorted(keys))

    def test_relationship_identifiers_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            analysis = ConstitutionalAnalysisEngine().analyze(self._fixture(Path(tmp) / "c1"))
            ids = [r.relationship_id for r in analysis.relationships]
            self.assertEqual(len(ids), len(set(ids)))

    def test_conflict_authority_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            analysis = ConstitutionalAnalysisEngine().analyze(self._fixture(Path(tmp) / "c1"))
            conflicts = [r for r in analysis.relationships if r.relationship_type == "contradicts"]
            self.assertTrue(conflicts)
            self.assertTrue(any(r.authority_resolution for r in conflicts))

    def test_reporter_writes_canonical_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            analysis = ConstitutionalAnalysisEngine().analyze(self._fixture(root / "c1"))
            written = ConstitutionalAnalysisReporter().write(analysis, root / "c2")
            names = {path.name for path in written}
            self.assertEqual(
                names,
                {
                    "constitutional_analysis.json",
                    "constitutional_graph.json",
                    "constitutional_conflicts.json",
                    "constitutional_duplicates.json",
                    "constitutional_concordance.json",
                    "constitutional_authority.json",
                    "constitutional_analysis_report.md",
                },
            )

    def test_output_json_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            analysis = ConstitutionalAnalysisEngine().analyze(self._fixture(root / "c1"))
            written = ConstitutionalAnalysisReporter().write(analysis, root / "c2")
            for path in written:
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
