from pathlib import Path

from dev.doctor.check import HealthCheck
from knowledge_engine.director.knowledge_director import KnowledgeDirector
from knowledge_engine.director.models import DirectorRequest


ROOT = Path(__file__).resolve().parents[2]


class KnowledgeDirectorCheck(HealthCheck):

    name = "Knowledge Director"
    category = "Knowledge"
    order = 50

    description = (
        "Verifies the Knowledge Director and Workflow Registry."
    )

    documentation = (
        "docs/architecture/architecture_blueprint.md"
    )

    def run(self):

        fixture = (
            ROOT
            / "dev/integration/fixtures/phase_ii_c_sample.txt"
        )

        director = KnowledgeDirector()

        #
        # Verify registered workflows
        #

        intents = director.registry.intents()

        if not intents:
            self.fail("Workflow registry is empty.")
            self.score(0)
            return self.result()

        self.detail("Registered Workflows:")

        for intent in intents:
            self.detail(f"  ✓ {intent}")

        #
        # Verify routing
        #

        response = director.handle(
            DirectorRequest(
                intent="ingest_fixture",
                source_path=fixture,
            )
        )

        if response.passed:

            self.detail(
                f"workflow={response.workflow}"
            )

            self.detail(
                f"chunks={response.metadata.get('chunks')}"
            )

            self.detail(
                f"embeddings={response.metadata.get('embeddings')}"
            )

            self.detail(
                "retrieval_verified="
                f"{response.metadata.get('retrieval_verified')}"
            )

            self.score(100)

        else:

            self.fail(response.message)

            for error in response.errors:
                self.fail(error)

            self.score(0)

        return self.result()
