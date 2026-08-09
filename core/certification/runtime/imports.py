from __future__ import annotations

import importlib
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModuleResolution:
    module: str
    imported: bool
    origin: str | None
    error: str | None = None


DEFAULT_MODULES = (
    "core",
    "core.src",
    "core.executive",
    "core.conversation",
    "core.knowledge_catalog",
)


def resolve_modules(
    modules: tuple[str, ...] = DEFAULT_MODULES,
) -> tuple[ModuleResolution, ...]:
    results: list[ModuleResolution] = []

    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
            results.append(
                ModuleResolution(
                    module=module_name,
                    imported=True,
                    origin=getattr(module, "__file__", None),
                )
            )
        except Exception as exc:
            results.append(
                ModuleResolution(
                    module=module_name,
                    imported=False,
                    origin=None,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )

    return tuple(results)
