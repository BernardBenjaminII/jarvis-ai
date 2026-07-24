from pathlib import Path

from dev.doctor.check import HealthCheck
from knowledge_engine.workflows.fixture_ingest import run_fixture_ingest


ROOT = Path(__file__).resolve().parents[2]


class KnowledgeWorkflowCheck(HealthCheck):
    name = "Knowledge Workflow"
    category = "Knowledge"
    order = 40

    description = "Runs the Phase 3A fixture ingest workflow."
    fix_hint = "Run python -m knowledge_engine.fixture_workflow_cli dev/integration/fixtures/phase_ii_c_sample.txt"
    documentation = "docs/architecture/architecture_blueprint.md"

    def run(self):
        fixture = ROOT / "dev/integration/fixtures/phase_ii_c_sample.txt"

        context, report = run_fixture_ingest(fixture)

        for stage in report.stages:
            if stage.passed:
                self.detail(f"✓ {stage.name}")
            else:
                self.fail(f"{stage.name} failed")
                for error in stage.errors:
                    self.fail(error)

        if context.ok and report.passed:
            self.detail(f"chunks={len(context.chunks)}")
            self.detail(f"embeddings={len(context.embeddings)}")
            self.detail(f"registry_ids={len(context.registry_ids)}")
            self.score(100)
        else:
            self.score(0)

        return self.result()
