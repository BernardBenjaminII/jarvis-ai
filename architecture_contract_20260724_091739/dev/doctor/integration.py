from dev.doctor.check import HealthCheck
from dev.integration.knowledge_pipeline_check import KnowledgePipelineIntegrationCheck


class KnowledgeIntegrationCheck(HealthCheck):
    name = "Knowledge Integration"
    category = "Knowledge"
    order = 35

    description = "Verifies the Phase II-C Knowledge Engine integration harness."
    fix_hint = "Run ./dev/verify_phase_ii_c.sh and inspect failing stages."
    documentation = "docs/architecture/architecture_blueprint.md"

    def run(self):
        check = KnowledgePipelineIntegrationCheck()
        ok = check.run()

        for result in check.results:
            if result.passed:
                self.detail(f"✓ {result.name}")
            else:
                self.fail(f"{result.name} failed")
                for error in result.errors:
                    self.fail(error)

        self.score(100 if ok else 0)
        return self.result()
