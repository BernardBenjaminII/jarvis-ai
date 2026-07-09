from dev.doctor.check import HealthCheck

from knowledge_engine.director.knowledge_director import KnowledgeDirector
from knowledge_engine.director.models import DirectorRequest


class SearchWorkflowCheck(HealthCheck):

    name = "Search Workflow"
    category = "Knowledge"
    order = 55

    description = (
        "Verifies the Director can route a search workflow."
    )

    documentation = (
        "docs/architecture/service_architecture.md"
    )

    def run(self):

        response = KnowledgeDirector().handle(
            DirectorRequest(
                intent="search",
                query="JARVIS",
            )
        )

        if response.passed:

            self.detail(
                f"workflow={response.workflow}"
            )

            self.detail(
                f"results={response.metadata.get('result_count', 0)}"
            )

            self.score(100)

        else:

            self.fail(response.message)

            for error in response.errors:
                self.fail(error)

            self.score(0)

        return self.result()
