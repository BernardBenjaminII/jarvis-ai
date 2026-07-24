"""Deterministic API inventory for packages, modules, and namespaces."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

from core.architecture import architecture_fingerprint, canonical_json

from .errors import EngineeringValidationError
from .import_resolution import PythonImportResolver
from .inventory_targets import InventoryTarget, InventoryTargetKind
from .public_surface import evaluate_public_surface


@dataclass(frozen=True, slots=True)
class PublicSymbol:
    target: str
    symbol: str
    declared_in: str
    implementation_candidates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "implementation_candidates",
            tuple(sorted(set(self.implementation_candidates))),
        )


@dataclass(frozen=True, slots=True)
class TargetAPIInventory:
    target: InventoryTarget
    exported_symbols: tuple[PublicSymbol, ...]
    discovered_definitions: tuple[PublicSymbol, ...]
    parse_findings: tuple[str, ...] = ()

    @property
    def import_name(self) -> str:
        return self.target.import_name

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


PackageAPIInventory = TargetAPIInventory


def _tree(path: Path) -> ast.Module:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise EngineeringValidationError(f"Unable to parse {path}: {exc}") from exc


def _module_name(root: Path, path: Path) -> str:
    parts = list(path.relative_to(root).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _definitions(tree: ast.Module) -> tuple[str, ...]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    names.add(target.id)
    return tuple(sorted(names))


def _imports(tree: ast.Module) -> tuple[str, ...]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return tuple(sorted(name for name in names if not name.startswith("_")))


def _module_path(root: Path, module_name: str) -> tuple[Path, bool] | None:
    relative = Path(*module_name.split("."))
    module_file = root / relative.with_suffix(".py")
    package_file = root / relative / "__init__.py"

    if module_file.is_file():
        return module_file, False
    if package_file.is_file():
        return package_file, True
    return None


def _public_surface(
    root: Path,
    path: Path,
    module_name: str,
    *,
    is_package: bool,
) -> tuple[tuple[str, ...], bool, tuple[str, ...]]:
    cache: dict[str, tuple[str, ...] | None] = {}
    visiting: set[str] = set()

    def resolve_imported_all(import_name: str) -> tuple[str, ...] | None:
        if import_name in cache:
            return cache[import_name]
        if import_name in visiting:
            return None

        resolved_path = _module_path(root, import_name)
        if resolved_path is None:
            cache[import_name] = None
            return None

        imported_path, imported_is_package = resolved_path
        visiting.add(import_name)
        try:
            result = evaluate_public_surface(
                _tree(imported_path),
                module_name=import_name,
                is_package=imported_is_package,
                imported_all_resolver=resolve_imported_all,
            )
        finally:
            visiting.remove(import_name)

        cache[import_name] = result.symbols if result.resolved else None
        return cache[import_name]

    result = evaluate_public_surface(
        _tree(path),
        module_name=module_name,
        is_package=is_package,
        imported_all_resolver=resolve_imported_all,
    )
    return result.symbols, result.resolved, result.findings


def _package_index(root: Path, package_dir: Path) -> dict[str, tuple[str, ...]]:
    index: dict[str, set[str]] = {}
    for path in sorted(package_dir.rglob("*.py")):
        module = _module_name(root, path)
        for symbol in _definitions(_tree(path)):
            index.setdefault(symbol, set()).add(module)
    return {
        symbol: tuple(sorted(modules))
        for symbol, modules in sorted(index.items())
    }


def _inventory_file(
    root: Path,
    target: InventoryTarget,
    path: Path,
    index: Mapping[str, tuple[str, ...]],
    *,
    is_package: bool,
) -> TargetAPIInventory:
    tree = _tree(path)
    explicit, resolved, surface_findings = _public_surface(
        root,
        path,
        target.canonical_import_name,
        is_package=is_package,
    )

    findings: list[str] = list(surface_findings)
    public = explicit

    if not resolved:
        public = tuple(sorted(set(_definitions(tree)) | set(_imports(tree))))
        findings.append(
            "Public surface derived from non-private imports and definitions."
        )

    exported = tuple(
        PublicSymbol(
            target=target.import_name,
            symbol=name,
            declared_in=target.canonical_import_name,
            implementation_candidates=index.get(name, ()),
        )
        for name in sorted(set(public))
    )
    discovered = tuple(
        PublicSymbol(
            target=target.import_name,
            symbol=name,
            declared_in=modules[0],
            implementation_candidates=modules,
        )
        for name, modules in sorted(index.items())
    )
    return TargetAPIInventory(
        target=target,
        exported_symbols=exported,
        discovered_definitions=discovered,
        parse_findings=tuple(dict.fromkeys(findings)),
    )


def inventory_target(
    project_root: Path,
    import_name: str,
    aliases: Mapping[str, str] | None = None,
) -> TargetAPIInventory:
    root = project_root.resolve()
    target = PythonImportResolver(root, aliases).resolve(import_name).target

    if target.kind == InventoryTargetKind.MISSING:
        return TargetAPIInventory(
            target=target,
            exported_symbols=(),
            discovered_definitions=(),
            parse_findings=("Import target could not be resolved.",),
        )

    if target.path is None:
        raise EngineeringValidationError(f"Resolved target has no path: {import_name}")

    path = root / target.path
    kind = target.kind

    if kind == InventoryTargetKind.COMPATIBILITY_ALIAS:
        if path.is_file():
            kind = InventoryTargetKind.MODULE
        elif (path / "__init__.py").is_file():
            kind = InventoryTargetKind.PACKAGE
        else:
            kind = InventoryTargetKind.NAMESPACE_PACKAGE

    if kind == InventoryTargetKind.MODULE:
        module_name = target.canonical_import_name
        index = {name: (module_name,) for name in _definitions(_tree(path))}
        return _inventory_file(
            root,
            target,
            path,
            index,
            is_package=False,
        )

    index = _package_index(root, path)

    if kind == InventoryTargetKind.PACKAGE:
        return _inventory_file(
            root,
            target,
            path / "__init__.py",
            index,
            is_package=True,
        )

    discovered = tuple(
        PublicSymbol(
            target=target.import_name,
            symbol=name,
            declared_in=modules[0],
            implementation_candidates=modules,
        )
        for name, modules in sorted(index.items())
    )
    return TargetAPIInventory(
        target=target,
        exported_symbols=(),
        discovered_definitions=discovered,
        parse_findings=(
            "Namespace package has no initializer-defined public surface.",
        ),
    )


def inventory_targets(
    project_root: Path,
    import_names: Iterable[str],
    aliases: Mapping[str, str] | None = None,
) -> tuple[TargetAPIInventory, ...]:
    return tuple(
        inventory_target(project_root, name, aliases)
        for name in sorted(set(import_names))
    )


def inventory_package(project_root: Path, package: str) -> TargetAPIInventory:
    return inventory_target(project_root, package)


def inventory_packages(
    project_root: Path,
    packages: Iterable[str],
) -> tuple[TargetAPIInventory, ...]:
    return inventory_targets(project_root, packages)


def discover_definition_index(
    project_root: Path,
    package_root: Path,
) -> dict[str, tuple[str, ...]]:
    return _package_index(project_root.resolve(), package_root.resolve())


__all__ = [
    "PackageAPIInventory",
    "PublicSymbol",
    "TargetAPIInventory",
    "discover_definition_index",
    "inventory_package",
    "inventory_packages",
    "inventory_target",
    "inventory_targets",
]
