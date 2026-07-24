"""Static Python import resolution without runtime imports."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from .inventory_targets import (
    InventoryResolution,
    InventoryTarget,
    InventoryTargetKind,
    import_name_to_relative_path,
    normalize_import_name,
)


class PythonImportResolver:
    def __init__(
        self,
        project_root: Path,
        aliases: Mapping[str, str] | None = None,
    ) -> None:
        self._project_root = project_root.resolve()
        self._aliases = {
            normalize_import_name(source): normalize_import_name(target)
            for source, target in sorted((aliases or {}).items())
        }

    @property
    def project_root(self) -> Path:
        return self._project_root

    def resolve(self, import_name: str) -> InventoryResolution:
        requested = normalize_import_name(import_name)
        canonical = self._aliases.get(requested, requested)
        trace = [f"requested:{requested}"]
        if canonical != requested:
            trace.append(f"alias:{requested}->{canonical}")

        relative = import_name_to_relative_path(canonical)
        directory = self._project_root / relative
        module = self._project_root / f"{relative}.py"
        alias = canonical != requested

        if directory.is_dir() and (directory / "__init__.py").is_file():
            trace.append("resolved:package")
            return InventoryResolution(
                requested_import=requested,
                target=InventoryTarget(
                    import_name=requested,
                    kind=InventoryTargetKind.COMPATIBILITY_ALIAS if alias else InventoryTargetKind.PACKAGE,
                    path=str(directory.relative_to(self._project_root)),
                    package_root=str(directory.relative_to(self._project_root)),
                    exists=True,
                    canonical_import_name=canonical,
                    evidence=(
                        f"directory:{directory.relative_to(self._project_root)}",
                        f"initializer:{(directory / '__init__.py').relative_to(self._project_root)}",
                    ),
                ),
                resolution_trace=tuple(trace),
            )

        if module.is_file():
            trace.append("resolved:module")
            return InventoryResolution(
                requested_import=requested,
                target=InventoryTarget(
                    import_name=requested,
                    kind=InventoryTargetKind.COMPATIBILITY_ALIAS if alias else InventoryTargetKind.MODULE,
                    path=str(module.relative_to(self._project_root)),
                    package_root=str(module.parent.relative_to(self._project_root)),
                    exists=True,
                    canonical_import_name=canonical,
                    evidence=(f"module:{module.relative_to(self._project_root)}",),
                ),
                resolution_trace=tuple(trace),
            )

        if directory.is_dir():
            trace.append("resolved:namespace_package")
            return InventoryResolution(
                requested_import=requested,
                target=InventoryTarget(
                    import_name=requested,
                    kind=InventoryTargetKind.COMPATIBILITY_ALIAS if alias else InventoryTargetKind.NAMESPACE_PACKAGE,
                    path=str(directory.relative_to(self._project_root)),
                    package_root=str(directory.relative_to(self._project_root)),
                    exists=True,
                    canonical_import_name=canonical,
                    evidence=(f"namespace:{directory.relative_to(self._project_root)}",),
                ),
                resolution_trace=tuple(trace),
            )

        trace.append("resolved:missing")
        return InventoryResolution(
            requested_import=requested,
            target=InventoryTarget(
                import_name=requested,
                kind=InventoryTargetKind.MISSING,
                path=None,
                package_root=None,
                exists=False,
                canonical_import_name=canonical,
            ),
            resolution_trace=tuple(trace),
        )


def resolve_import_target(
    project_root: Path,
    import_name: str,
    aliases: Mapping[str, str] | None = None,
) -> InventoryResolution:
    return PythonImportResolver(project_root, aliases).resolve(import_name)


__all__ = ["PythonImportResolver", "resolve_import_target"]
