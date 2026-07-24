"""Recursive capability package discovery."""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Iterable

from core.capabilities.registry import CapabilityRegistry


@dataclass(frozen=True)
class CapabilityDiscoveryResult:
    module: str
    discovered: bool
    loaded: bool
    registered_before: int
    registered_after: int
    error: str | None = None

    @property
    def registered_count(self) -> int:
        return self.registered_after - self.registered_before


class CapabilityDiscovery:
    """Discover and invoke ``register_capabilities`` hooks deterministically."""

    def __init__(self, package_roots: Iterable[str]) -> None:
        self.package_roots = tuple(
            sorted({
                package.strip()
                for package in package_roots
                if package and package.strip()
            })
        )

    @staticmethod
    def _module_names(root_name: str) -> list[str]:
        root = importlib.import_module(root_name)
        names = {root.__name__}

        if hasattr(root, "__path__"):
            for module in pkgutil.walk_packages(
                root.__path__,
                prefix=f"{root.__name__}.",
            ):
                names.add(module.name)

        return sorted(names)

    @staticmethod
    def _register(
        module: ModuleType,
        registry: CapabilityRegistry,
    ) -> tuple[bool, int, int]:
        hook = getattr(module, "register_capabilities", None)
        before = len(registry.all())

        if not callable(hook):
            return False, before, before

        hook(registry)
        after = len(registry.all())
        return True, before, after

    def discover(
        self,
        registry: CapabilityRegistry,
    ) -> list[CapabilityDiscoveryResult]:
        results: list[CapabilityDiscoveryResult] = []

        for root_name in self.package_roots:
            try:
                module_names = self._module_names(root_name)
            except Exception as exc:
                current = len(registry.all())
                results.append(
                    CapabilityDiscoveryResult(
                        module=root_name,
                        discovered=False,
                        loaded=False,
                        registered_before=current,
                        registered_after=current,
                        error=str(exc),
                    )
                )
                continue

            for module_name in module_names:
                before = len(registry.all())

                try:
                    module = importlib.import_module(module_name)
                    discovered, before, after = self._register(
                        module,
                        registry,
                    )
                    results.append(
                        CapabilityDiscoveryResult(
                            module=module_name,
                            discovered=discovered,
                            loaded=True,
                            registered_before=before,
                            registered_after=after,
                        )
                    )
                except Exception as exc:
                    results.append(
                        CapabilityDiscoveryResult(
                            module=module_name,
                            discovered=False,
                            loaded=False,
                            registered_before=before,
                            registered_after=len(registry.all()),
                            error=str(exc),
                        )
                    )

        return results
