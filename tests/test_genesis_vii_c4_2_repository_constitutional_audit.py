from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.governance.constitution.repository_audit import (
    RepositoryConstitutionalAuditEngine,
    RepositoryConstitutionalAuditReporter,
    default_repository_audit_policy,
    discover_repository_artifacts,
)


ARTICLE = {
    "article_id": "ARTICLE-0001",
    "canonical_text": (
        "Constitutional evidence must remain preserved traceable reviewable "
        "deterministic attributable durable and available for governance."
    ),
    "domain": "governance",
    "status": "ratified",
    "authority": "constitution",
    "authority_rank": 1,
    "fingerprint": "article-fingerprint",
}


def write_ratification(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "constitutional_ratification.json").write_text(
        json.dumps(
            {
                "repository_fingerprint": "repo",
                "extraction_fingerprint": "extract",
                "analysis_fingerprint": "analysis",
                "ratification_fingerprint": "ratify",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (directory / "constitutional_registry.json").write_text(
        json.dumps({"articles": [ARTICLE]}, indent=2),
        encoding="utf-8",
    )


def write_repository(directory: Path) -> None:
    (directory / "docs/decisions").mkdir(parents=True)
    (directory / "docs/decisions/ADR-0001.md").write_text(
        ARTICLE["canonical_text"],
        encoding="utf-8",
    )
    (directory / "docs/unrelated.md").write_text(
        "quartz zephyr nebula xylophone",
        encoding="utf-8",
    )
    (directory / ".git").mkdir()
    (directory / ".git/ignored.md").write_text(
        ARTICLE["canonical_text"],
        encoding="utf-8",
    )


class RepositoryConstitutionalAuditTests(unittest.TestCase):
    def test_discovery_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_repository(root)
            policy = default_repository_audit_policy()
            first = discover_repository_artifacts(root, policy)
            second = discover_repository_artifacts(root, policy)
        self.assertEqual(first, second)

    def test_excluded_directories_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_repository(root)
            artifacts = discover_repository_artifacts(
                root,
                default_repository_audit_policy(),
            )
        self.assertEqual(len(artifacts), 2)
        self.assertFalse(any(".git/" in item.path for item in artifacts))

    def test_all_discovered_artifacts_are_evaluated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            ratification = root / "ratification"
            repository.mkdir()
            write_repository(repository)
            write_ratification(ratification)
            result = RepositoryConstitutionalAuditEngine().assess(
                repository_root=repository,
                ratification_directory=ratification,
                compliance_fingerprint="comply",
                certification_fingerprint="certify",
            )
        self.assertEqual(
            result.statistics.artifacts_discovered,
            result.statistics.artifacts_evaluated,
        )

    def test_compliant_and_not_applicable_are_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            ratification = root / "ratification"
            repository.mkdir()
            write_repository(repository)
            write_ratification(ratification)
            result = RepositoryConstitutionalAuditEngine().assess(
                repository_root=repository,
                ratification_directory=ratification,
                compliance_fingerprint="comply",
                certification_fingerprint="certify",
            )
        self.assertEqual(result.statistics.compliant_artifacts, 1)
        self.assertEqual(result.statistics.not_applicable_artifacts, 1)

    def test_article_usage_is_computed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            ratification = root / "ratification"
            repository.mkdir()
            write_repository(repository)
            write_ratification(ratification)
            result = RepositoryConstitutionalAuditEngine().assess(
                repository_root=repository,
                ratification_directory=ratification,
                compliance_fingerprint="comply",
                certification_fingerprint="certify",
            )
        self.assertEqual(len(result.article_usage), 1)
        self.assertGreaterEqual(result.article_usage[0].reference_count, 1)

    def test_audit_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            ratification = root / "ratification"
            repository.mkdir()
            write_repository(repository)
            write_ratification(ratification)
            engine = RepositoryConstitutionalAuditEngine()
            kwargs = {
                "repository_root": repository,
                "ratification_directory": ratification,
                "compliance_fingerprint": "comply",
                "certification_fingerprint": "certify",
            }
            first = engine.assess(**kwargs)
            second = engine.assess(**kwargs)
        self.assertEqual(first.audit_fingerprint, second.audit_fingerprint)
        self.assertEqual(first.assessments, second.assessments)

    def test_identifiers_are_unique(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_repository(root)
            artifacts = discover_repository_artifacts(
                root,
                default_repository_audit_policy(),
            )
        identifiers = [item.artifact_id for item in artifacts]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_reporter_writes_eight_canonical_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            ratification = root / "ratification"
            output = root / "output"
            repository.mkdir()
            write_repository(repository)
            write_ratification(ratification)
            result = RepositoryConstitutionalAuditEngine().assess(
                repository_root=repository,
                ratification_directory=ratification,
                compliance_fingerprint="comply",
                certification_fingerprint="certify",
            )
            written = RepositoryConstitutionalAuditReporter().write(
                result,
                output,
            )
            for path in written:
                if path.suffix == ".json":
                    json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(written), 8)


if __name__ == "__main__":
    unittest.main()
