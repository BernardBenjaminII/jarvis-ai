from __future__ import annotations

from knowledge_engine.director.models import (
    DirectorRequest,
    DirectorResponse,
)
from knowledge_engine.director.workflow_registry import WorkflowRegistry


class KnowledgeDirector:

    def __init__(self):

        self.registry = WorkflowRegistry()

    def handle(
        self,
        request: DirectorRequest,
    ) -> DirectorResponse:

        workflow = self.registry.get(
            request.intent
        )

        if workflow is None:

            return DirectorResponse(
                intent=request.intent,
                workflow="none",
                passed=False,
                message="Unknown workflow.",
                errors=[
                    f"No workflow registered for '{request.intent}'"
                ],
            )

        return workflow.run(request)
