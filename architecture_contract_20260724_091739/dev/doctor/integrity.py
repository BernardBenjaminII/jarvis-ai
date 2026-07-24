from pathlib import Path

from dev.doctor.check import HealthCheck
from knowledge_engine.integrity.auditor import KnowledgeIntegrityAuditor


DEFAULT_DB = Path(
    "/media/abdullah/JARVIS_RUNTIME_L/knowledge/catalog.sqlite"
)


class KnowledgeIntegrityCheck(HealthCheck):
    name = "Knowledge Integrity"
    category = "Knowledge"
    order = 75

    description = (
        "Audits persisted document text, chunks, and embeddings."
    )

    documentation = (
        "docs/architecture/service_architecture.md"
    )

    def run(self):
        report = KnowledgeIntegrityAuditor(DEFAULT_DB).run(
            document_limit=25,
            chunk_limit=100,
        )

        self.detail(
            f"documents_checked={report.documents_checked}"
        )

        self.detail(
            f"chunks_checked={report.chunks_checked}"
        )

        self.detail(
            f"embeddings_checked={report.embeddings_checked}"
        )

        self.detail(
            f"warnings={len(report.warnings)}"
        )

        if report.errors:
            for issue in report.errors[:5]:
                location = issue.file_path or issue.record_id or "unknown"

                self.fail(
                    f"{issue.stage}: {issue.message} [{location}]"
                )

            self.score(0)
        else:
            self.score(100)

        return self.result()
