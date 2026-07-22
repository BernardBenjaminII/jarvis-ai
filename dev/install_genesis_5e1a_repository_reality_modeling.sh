#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

test -f core/engineering/constitution.py || {
    echo "ERROR: Genesis V-E0 is required."
    exit 1
}

mkdir -p core/engineering docs/engineering tests dev/verification

cat > core/engineering/inventory_targets.py <<'PYEOF'
"""Repository-reality contracts for importable engineering artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.architecture import architecture_fingerprint, canonical_json
from .errors import EngineeringValidationError


class InventoryTargetKind:
    PACKAGE = "package"
    MODULE = "module"
    NAMESPACE_PACKAGE = "namespace_package"
    COMPATIBILITY_ALIAS = "compatibility_alias"
    MISSING = "missing"


_VALID_KINDS = {
    InventoryTargetKind.PACKAGE,
    InventoryTargetKind.MODULE,
    InventoryTargetKind.NAMESPACE_PACKAGE,
    InventoryTargetKind.COMPATIBILITY_ALIAS,
    InventoryTargetKind.MISSING,
}


def _required(value: str, name: str) -> str:
    result = value.strip()
    if not result:
        raise EngineeringValidationError(f"{name} must not be empty")
    return result


def normalize_import_name(import_name: str) -> str:
    parts = [part.strip() for part in _required(import_name, "import_name").split(".")]
    if any(not part for part in parts):
        raise EngineeringValidationError(f"Invalid import name: {import_name!r}")
    return ".".join(parts)


def import_name_to_relative_path(import_name: str) -> Path:
    return Path(*normalize_import_name(import_name).split("."))


@dataclass(frozen=True, slots=True)
class InventoryTarget:
    import_name: str
    kind: str
    path: str | None
    package_root: str | None
    exists: bool
    canonical_import_name: str
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "import_name", normalize_import_name(self.import_name))
        object.__setattr__(
            self,
            "canonical_import_name",
            normalize_import_name(self.canonical_import_name),
        )
        if self.kind not in _VALID_KINDS:
            raise EngineeringValidationError(f"Unsupported target kind: {self.kind}")
        object.__setattr__(self, "evidence", tuple(sorted(set(self.evidence))))

    def to_canonical_json(self) -> str:
        return canonical_json(self)

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


@dataclass(frozen=True, slots=True)
class InventoryResolution:
    requested_import: str
    target: InventoryTarget
    resolution_trace: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "requested_import",
            normalize_import_name(self.requested_import),
        )
        object.__setattr__(self, "resolution_trace", tuple(self.resolution_trace))

    def fingerprint(self) -> str:
        return architecture_fingerprint(self)


def stable_inventory_targets(
    targets: Iterable[InventoryTarget],
) -> tuple[InventoryTarget, ...]:
    return tuple(
        sorted(
            targets,
            key=lambda item: (item.import_name, item.kind, item.path or ""),
        )
    )


__all__ = [
    "InventoryResolution",
    "InventoryTarget",
    "InventoryTargetKind",
    "import_name_to_relative_path",
    "normalize_import_name",
    "stable_inventory_targets",
]
PYEOF

cat > core/engineering/import_resolution.py <<'PYEOF'
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
PYEOF

cat > core/engineering/api_inventory.py <<'PYEOF'
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


def _literal_all(tree: ast.Module) -> tuple[str, ...]:
    names: set[str] = set()
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            continue
        if isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
            for item in node.value.elts:
                if isinstance(item, ast.Constant) and isinstance(item.value, str):
                    names.add(item.value)
    return tuple(sorted(names))


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
) -> TargetAPIInventory:
    tree = _tree(path)
    explicit = _literal_all(tree)
    findings: list[str] = []
    public = explicit
    if not public:
        public = tuple(sorted(set(_definitions(tree)) | set(_imports(tree))))
        findings.append(
            "No literal __all__; surface derived from non-private imports and definitions."
        )

    exported = tuple(
        PublicSymbol(
            target=target.import_name,
            symbol=name,
            declared_in=target.canonical_import_name,
            implementation_candidates=index.get(name, ()),
        )
        for name in public
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
        parse_findings=tuple(findings),
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
        return _inventory_file(root, target, path, index)

    index = _package_index(root, path)
    if kind == InventoryTargetKind.PACKAGE:
        return _inventory_file(root, target, path / "__init__.py", index)

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
        parse_findings=("Namespace package has no initializer-defined public surface.",),
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
PYEOF

# Compatibility analyzer: replace package-only assumptions with target-aware behavior.
"${PYTHON_BIN}" - <<'PYEOF'
from pathlib import Path

path = Path("core/engineering/compatibility.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from .api_inventory import PackageAPIInventory",
    "from .api_inventory import TargetAPIInventory",
)
text = text.replace(
    "inventories: tuple[PackageAPIInventory, ...]",
    "inventories: tuple[TargetAPIInventory, ...]",
)
text = text.replace(
    "by_package: Mapping[str, PackageAPIInventory] = {\n        item.package: item for item in inventories\n    }",
    "by_package: Mapping[str, TargetAPIInventory] = {\n        item.import_name: item for item in inventories\n    }",
)
text = text.replace(
    "tuple(sorted(inventories, key=lambda item: item.package))",
    "tuple(sorted(inventories, key=lambda item: item.import_name))",
)
path.write_text(text, encoding="utf-8")
PYEOF

# CLI: use generalized target inventory.
"${PYTHON_BIN}" - <<'PYEOF'
from pathlib import Path

path = Path("core/engineering/cli.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    "from .api_inventory import inventory_packages",
    "from .api_inventory import inventory_targets",
)
text = text.replace(
    "inventories = inventory_packages(root, packages)",
    "inventories = inventory_targets(root, packages)",
)
path.write_text(text, encoding="utf-8")
PYEOF

# Public API: preserve V-E0/V-E1 exports while adding V-E1A.
"${PYTHON_BIN}" - <<'PYEOF'
from pathlib import Path

path = Path("core/engineering/__init__.py")
text = path.read_text(encoding="utf-8")

text = text.replace(
    "    PackageAPIInventory,\n",
    "    PackageAPIInventory,\n    TargetAPIInventory,\n",
)
text = text.replace(
    "    inventory_packages,\n)",
    "    inventory_packages,\n    inventory_target,\n    inventory_targets,\n)",
    1,
)

extra_imports = """from .import_resolution import (
    PythonImportResolver,
    resolve_import_target,
)
from .inventory_targets import (
    InventoryResolution,
    InventoryTarget,
    InventoryTargetKind,
    import_name_to_relative_path,
    normalize_import_name,
    stable_inventory_targets,
)
"""
if "from .import_resolution import" not in text:
    text = text.replace("from .reporting import (\n", extra_imports + "from .reporting import (\n")

names = [
    "InventoryResolution",
    "InventoryTarget",
    "InventoryTargetKind",
    "PythonImportResolver",
    "TargetAPIInventory",
    "import_name_to_relative_path",
    "inventory_target",
    "inventory_targets",
    "normalize_import_name",
    "resolve_import_target",
    "stable_inventory_targets",
]
for name in names:
    token = f'"{name}"'
    if token not in text:
        text = text.replace("__all__ = [\n", f'__all__ = [\n    "{name}",\n', 1)

path.write_text(text, encoding="utf-8")
PYEOF

cat > docs/engineering/genesis_v_e1a_repository_reality_modeling.md <<'EOF'
# Genesis V-E1A — Repository Reality Modeling

## Mission

Replace the package-directory assumption with an explicit model of Python
repository reality.

## Target Kinds

- package
- module
- namespace package
- compatibility alias
- missing target

## Resolution

For `core.example.item`, static resolution checks:

1. `core/example/item/__init__.py`
2. `core/example/item.py`
3. `core/example/item/` as a namespace
4. configured compatibility aliases
5. a first-class missing target

No analyzed module is imported or executed.

## Engineering Principle

Reality precedes the model. Unexpected repository states become evidence rather
than unhandled exceptions.

## Compatibility Integration

V-E1 now inventories import targets rather than assuming every test import names
a package directory. Module imports such as
`core.cognition.common.cognitive_object` are therefore analyzed correctly.
EOF

cat > tests/test_genesis_5e1a_repository_reality_modeling.py <<'PYEOF'
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.engineering import (
    InventoryTargetKind,
    PythonImportResolver,
    inventory_target,
)


class RepositoryRealityModelingTests(unittest.TestCase):
    def _root(self, directory: str) -> Path:
        root = Path(directory)
        core = root / "core"
        core.mkdir()
        (core / "__init__.py").write_text("", encoding="utf-8")
        return root

    def test_resolves_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            package = root / "core" / "pkg"
            package.mkdir()
            (package / "__init__.py").write_text("", encoding="utf-8")
            result = PythonImportResolver(root).resolve("core.pkg")
            self.assertEqual(result.target.kind, InventoryTargetKind.PACKAGE)

    def test_resolves_and_inventories_module(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "core" / "item.py").write_text(
                'class Item:\n    pass\n\n__all__ = ["Item"]\n',
                encoding="utf-8",
            )
            result = PythonImportResolver(root).resolve("core.item")
            self.assertEqual(result.target.kind, InventoryTargetKind.MODULE)
            inventory = inventory_target(root, "core.item")
            self.assertEqual(
                tuple(item.symbol for item in inventory.exported_symbols),
                ("Item",),
            )

    def test_resolves_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            namespace = root / "core" / "namespace"
            namespace.mkdir()
            (namespace / "child.py").write_text("VALUE = 1\n", encoding="utf-8")
            result = PythonImportResolver(root).resolve("core.namespace")
            self.assertEqual(
                result.target.kind,
                InventoryTargetKind.NAMESPACE_PACKAGE,
            )

    def test_missing_target_is_inventory_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            result = inventory_target(root, "core.absent")
            self.assertEqual(result.target.kind, InventoryTargetKind.MISSING)
            self.assertEqual(result.exported_symbols, ())

    def test_resolves_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "core" / "canonical.py").write_text(
                "class Value:\n    pass\n",
                encoding="utf-8",
            )
            result = PythonImportResolver(
                root,
                {"core.legacy": "core.canonical"},
            ).resolve("core.legacy")
            self.assertEqual(
                result.target.kind,
                InventoryTargetKind.COMPATIBILITY_ALIAS,
            )

    def test_resolution_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self._root(directory)
            (root / "core" / "stable.py").write_text("VALUE = 1\n", encoding="utf-8")
            resolver = PythonImportResolver(root)
            self.assertEqual(
                resolver.resolve("core.stable").fingerprint(),
                resolver.resolve("core.stable").fingerprint(),
            )


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_5e1a_repository_reality_modeling.py <<'PYEOF'
#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=False,
        capture_output=False,
        text=True,
    )


def main() -> int:
    failures = 0
    required = (
        ROOT / "core/engineering/inventory_targets.py",
        ROOT / "core/engineering/import_resolution.py",
        ROOT / "core/engineering/api_inventory.py",
        ROOT / "docs/engineering/genesis_v_e1a_repository_reality_modeling.md",
        ROOT / "tests/test_genesis_5e1a_repository_reality_modeling.py",
    )
    failures += check(all(path.is_file() for path in required), "V-E1A required files")
    failures += check(
        run(
            "-m",
            "compileall",
            "-q",
            "core/engineering",
            "tests/test_genesis_5e1a_repository_reality_modeling.py",
        ).returncode == 0,
        "V-E1A compilation",
    )
    failures += check(
        run(
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5e1a_repository_reality_modeling",
        ).returncode == 0,
        "V-E1A unit tests",
    )

    source = (
        (ROOT / "core/engineering/import_resolution.py").read_text(encoding="utf-8")
        + (ROOT / "core/engineering/api_inventory.py").read_text(encoding="utf-8")
    )
    failures += check(
        "importlib" not in source
        and "subprocess" not in source
        and "exec(" not in source
        and "eval(" not in source,
        "Static non-executing resolution boundary",
    )

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        core = root / "core"
        pkg = core / "pkg"
        core.mkdir()
        pkg.mkdir()
        (core / "__init__.py").write_text("", encoding="utf-8")
        (core / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
        (pkg / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
        smoke = (
            "from pathlib import Path;"
            "from core.engineering import PythonImportResolver;"
            f"r=Path({str(root)!r});x=PythonImportResolver(r);"
            "a=x.resolve('core.module');b=x.resolve('core.pkg');"
            "c=x.resolve('core.missing');"
            "assert a.target.kind=='module';"
            "assert b.target.kind=='package';"
            "assert c.target.kind=='missing';"
            "print(a.fingerprint(),b.fingerprint(),c.fingerprint())"
        )
        first = subprocess.run(
            [sys.executable, "-c", smoke],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        second = subprocess.run(
            [sys.executable, "-c", smoke],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        failures += check(
            first.returncode == 0
            and second.returncode == 0
            and first.stdout == second.stdout,
            "Deterministic target resolution",
        )

    failures += check(
        run("dev/verification/verify_genesis_5e1_public_api_compatibility.py").returncode == 0,
        "Genesis V-E1 regression",
    )
    failures += check(
        run("dev/verification/verify_genesis_5e0_engineering_os_foundation.py").returncode == 0,
        "Genesis V-E0 regression",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(f"Overall status: {'EXCELLENT' if failures == 0 else 'FAILED'}")
    print("=" * 72)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_5e1a.sh <<'SHEOF'
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"
cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E1A — REPOSITORY REALITY MODELING"
echo "========================================================================"

"${PYTHON_BIN}" dev/verification/verify_genesis_5e1a_repository_reality_modeling.py
SHEOF

chmod +x \
    dev/verify_genesis_5e1a.sh \
    dev/verification/verify_genesis_5e1a_repository_reality_modeling.py

"${PYTHON_BIN}" dev/verification/verify_genesis_5e1a_repository_reality_modeling.py

echo
echo "Genesis V-E1A installed and verified."
echo "Re-run the repository analysis:"
echo
echo "PYTHON_BIN=${PYTHON_BIN} ./dev/analyze_public_api_compatibility.sh"
