from __future__ import annotations

import json
import tempfile
from pathlib import Path

from core.governance.constitution.compliance import (
    CompliancePolicy,
    ConstitutionalComplianceEngine,
)

from .models import RepositoryArtifact, RepositoryAuditPolicy


def evaluate_repository_artifacts(
    *,
    artifacts: tuple[RepositoryArtifact, ...],
    ratification_directory: Path,
    policy: RepositoryAuditPolicy,
):
    payload = {
        "subjects": [
            {
                "subject_id": artifact.artifact_id,
                "subject_type": artifact.artifact_type,
                "path": artifact.path,
                "title": artifact.path,
                "content": artifact.content,
                "domain": artifact.domain,
            }
            for artifact in artifacts
        ]
    }

    with tempfile.TemporaryDirectory(prefix="jarvis-c4-2-") as temporary:
        subject_path = Path(temporary) / "repository_subjects.json"
        subject_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return ConstitutionalComplianceEngine().assess(
            ratification_directory=ratification_directory,
            subject_path=subject_path,
            policy=CompliancePolicy(
                minimum_match_score=policy.minimum_match_score,
                contradiction_threshold=policy.contradiction_threshold,
                require_ratified_articles_only=True,
                fail_on_unresolved_article=False,
            ),
        )
