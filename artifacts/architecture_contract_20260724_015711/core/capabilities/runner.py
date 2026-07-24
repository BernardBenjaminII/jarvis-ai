from __future__ import annotations

import time

from core.capabilities.models import CapabilityContext, CapabilityResult
from core.capabilities.registry import CapabilityRegistry


class CapabilityRunner:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def run(self, context: CapabilityContext) -> list[CapabilityResult]:
        results: list[CapabilityResult] = []

        for capability in self.registry.resolve():
            print()
            print("=" * 70)
            print(f"Capability: {capability.name}")
            print("=" * 70)

            start = time.perf_counter()

            try:
                result = capability.execute(context)
                result.elapsed = time.perf_counter() - start
            except Exception as exc:
                result = CapabilityResult(
                    name=capability.name,
                    success=False,
                    errors=[str(exc)],
                    elapsed=time.perf_counter() - start,
                )

            results.append(result)

            if not result.success:
                break

        return results
