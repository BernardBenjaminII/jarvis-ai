from __future__ import annotations

from core.capabilities.base import Capability
from core.capabilities.models import CapabilityContext
from core.capabilities.models import CapabilityResult

from knowledge_engine.objects.service import ObjectService


class ObjectCapability(Capability):

    name = "knowledge.objects"

    description = "Build Knowledge Objects"

    requires = {"discovery"}

    provides = {"objects"}

    order = 200

    def __init__(
        self,
        dry_run: bool = False,
    ):
        self.dry_run = dry_run

    def execute(
        self,
        context: CapabilityContext,
    ) -> CapabilityResult:

        service = ObjectService(
            context.database.db_path
        )

        metrics = service.run(
            root_filter=(
                str(context.root)
                if context.root is not None
                else None
            ),
            dry_run=self.dry_run,
        )

        context.metrics[self.name] = metrics

        return CapabilityResult(
            name=self.name,
            success=True,
            metrics=metrics,
        )
