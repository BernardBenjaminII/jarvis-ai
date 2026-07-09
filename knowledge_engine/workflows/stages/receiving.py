from __future__ import annotations

from pathlib import Path

from knowledge_engine.workflows.core.context import KnowledgeContext
from knowledge_engine.workflows.core.stage import WorkflowStage


class ReceivingStage(WorkflowStage):
    name = "Receiving"

    def run(self, context: KnowledgeContext) -> KnowledgeContext:
        source = Path(context.source_path)

        if not source.exists():
            context.fail(f"Source file does not exist: {source}")
            return context

        if not source.is_file():
            context.fail(f"Source path is not a file: {source}")
            return context

        context.source_path = source
        context.content_type = self._detect_content_type(source)
        context.metadata["filename"] = source.name
        context.metadata["suffix"] = source.suffix.lower()
        context.metadata["size_bytes"] = source.stat().st_size
        context.metadata["received"] = True

        return context

    def _detect_content_type(self, source: Path) -> str:
        suffix = source.suffix.lower()

        if suffix in {".txt", ".md", ".log"}:
            return "text/plain"

        if suffix == ".pdf":
            return "application/pdf"

        if suffix == ".docx":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        if suffix == ".html":
            return "text/html"

        return "application/octet-stream"
