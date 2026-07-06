from __future__ import annotations

from core.capabilities.base import Capability
from core.capabilities.models import CapabilityContext
from core.capabilities.models import CapabilityResult

from knowledge_engine.discovery.service import DiscoveryService


class DiscoveryCapability(Capability):

    name = "knowledge.discovery"

    description = "Discover knowledge resources"

    requires = set()

    provides = {"discovery"}

    order = 100

    def __init__(
        self,
        limit: int | None = None,
    ):
        self.limit = limit

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:

        service = DiscoveryService(
            context.database.db_path
        )

        counts = service.run(
            root_path=str(context.root),
            limit=self.limit,
        )

        context.metrics[self.name] = counts

        return CapabilityResult(
            name=self.name,
            success=True,
            metrics=counts,
        )
