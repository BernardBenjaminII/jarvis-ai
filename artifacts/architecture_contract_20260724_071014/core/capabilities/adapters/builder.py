from __future__ import annotations

from typing import Any

from core.capabilities.base import Capability
from core.capabilities.models import CapabilityContext, CapabilityResult


class BuilderCapability(Capability):
    def __init__(
        self,
        *,
        name: str,
        builder_cls: type,
        method_name: str,
        description: str = "",
        requires: set[str] | None = None,
        provides: set[str] | None = None,
        order: int = 1000,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.builder_cls = builder_cls
        self.method_name = method_name
        self.requires = requires or set()
        self.provides = provides or set()
        self.order = order
        self.kwargs = kwargs or {}

    def execute(self, context: CapabilityContext) -> CapabilityResult:
        if context.database is None:
            return CapabilityResult(
                name=self.name,
                success=False,
                errors=["CapabilityContext.database is required"],
            )

        builder = self.builder_cls(context.database)
        method = getattr(builder, self.method_name)

        result = method(**self.kwargs)

        if not isinstance(result, dict):
            result = {"result": result}

        errors = []
        success = True

        for key, value in result.items():
            if key.endswith("errors") and value:
                errors.append(f"{key}: {value}")
                success = False

        return CapabilityResult(
            name=self.name,
            success=success,
            metrics=result,
            errors=errors,
        )
