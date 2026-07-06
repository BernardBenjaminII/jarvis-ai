from __future__ import annotations

from core.capabilities.base import Capability
from core.capabilities.models import CapabilityContext
from core.capabilities.models import CapabilityResult

from knowledge_engine.registry.service import RegistryService


class KnowledgeRegistryCapability(Capability):

    name = "knowledge.registry"

    description = "Populate the Knowledge Registry"

    requires = {"objects"}

    provides = {"registry"}

    order = 300

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:

        metrics = RegistryService(
            context.database
        ).run(
            root_filter=(
                str(context.root)
                if context.root
                else None
            )
        )

        context.metrics[self.name] = metrics

        return CapabilityResult(
            name=self.name,
            success=True,
            metrics=metrics,
        )
