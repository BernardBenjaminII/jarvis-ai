from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType

from core.capabilities.registry import CapabilityRegistry


@dataclass(frozen=True)
class CapabilityLoadResult:
    module: str
    loaded: bool
    error: str | None = None


class CapabilityLoader:
    """
    Discovers capability packages and lets them self-register.

    A package participates by exposing:

        register_capabilities(registry: CapabilityRegistry) -> None
    """

    def __init__(self, package_roots: list[str]) -> None:
        self.package_roots = package_roots

    def load(self, registry: CapabilityRegistry) -> list[CapabilityLoadResult]:
        results: list[CapabilityLoadResult] = []

        for package_root in self.package_roots:
            try:
                package = importlib.import_module(package_root)
            except Exception as exc:
                results.append(
                    CapabilityLoadResult(
                        module=package_root,
                        loaded=False,
                        error=str(exc),
                    )
                )
                continue

            results.extend(self._load_package(package, registry))

        return results

    def _load_package(
        self,
        package: ModuleType,
        registry: CapabilityRegistry,
    ) -> list[CapabilityLoadResult]:
        results: list[CapabilityLoadResult] = []

        # First try the package itself.
        results.append(self._try_register(package, registry))

        # Then try child modules if this is a package.
        if not hasattr(package, "__path__"):
            return results

        prefix = package.__name__ + "."

        for module_info in pkgutil.iter_modules(package.__path__, prefix):
            module_name = module_info.name

            if module_name.endswith(".__pycache__"):
                continue

            try:
                module = importlib.import_module(module_name)
                results.append(self._try_register(module, registry))
            except Exception as exc:
                results.append(
                    CapabilityLoadResult(
                        module=module_name,
                        loaded=False,
                        error=str(exc),
                    )
                )

        return results

    def _try_register(
        self,
        module: ModuleType,
        registry: CapabilityRegistry,
    ) -> CapabilityLoadResult:
        hook = getattr(module, "register_capabilities", None)

        if hook is None:
            return CapabilityLoadResult(
                module=module.__name__,
                loaded=True,
                error=None,
            )

        try:
            hook(registry)
            return CapabilityLoadResult(
                module=module.__name__,
                loaded=True,
                error=None,
            )
        except Exception as exc:
            return CapabilityLoadResult(
                module=module.__name__,
                loaded=False,
                error=str(exc),
            )
