#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E1C — STATIC PUBLIC SURFACE ENGINE"
echo "========================================================================"

mkdir -p \
    core/engineering \
    dev/verification \
    docs/engineering \
    tests \
    .migration_backups/genesis_5e1c

timestamp="$(date +%Y%m%d_%H%M%S)"

cp core/engineering/api_inventory.py \
   ".migration_backups/genesis_5e1c/${timestamp}_api_inventory.py"

cat > core/engineering/public_surface.py <<'PYEOF'
"""Deterministic, non-executing evaluation of Python public API surfaces."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Callable, Mapping


ImportedAllResolver = Callable[[str], tuple[str, ...] | None]


@dataclass(frozen=True, slots=True)
class PublicSurfaceResult:
    """Result of statically evaluating a module's ``__all__`` contract."""

    symbols: tuple[str, ...]
    resolved: bool
    findings: tuple[str, ...] = ()


class StaticPublicSurfaceEvaluator:
    """Evaluate supported ``__all__`` construction patterns using AST only.

    The evaluator deliberately supports a constrained, deterministic subset of
    Python expressions. It never imports or executes repository code.
    """

    def __init__(
        self,
        *,
        module_name: str,
        is_package: bool,
        imported_all_resolver: ImportedAllResolver | None = None,
    ) -> None:
        self._module_name = module_name
        self._is_package = is_package
        self._resolver = imported_all_resolver
        self._environment: dict[str, tuple[str, ...]] = {}
        self._findings: list[str] = []

    def evaluate(self, tree: ast.Module) -> PublicSurfaceResult:
        """Evaluate statements in source order and return the final surface."""

        self._evaluate_statements(tree.body)
        symbols = self._environment.get("__all__")
        if symbols is None:
            return PublicSurfaceResult(
                symbols=(),
                resolved=False,
                findings=tuple(
                    dict.fromkeys(
                        (
                            *self._findings,
                            "No statically resolvable __all__ assignment.",
                        )
                    )
                ),
            )

        return PublicSurfaceResult(
            symbols=self._deduplicate(symbols),
            resolved=True,
            findings=tuple(dict.fromkeys(self._findings)),
        )

    def _evaluate_statements(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(statement, ast.ImportFrom):
                self._evaluate_import_from(statement)
            elif isinstance(statement, ast.Assign):
                value = self._evaluate_expression(statement.value)
                if value is not None:
                    for target in statement.targets:
                        self._assign(target, value)
            elif isinstance(statement, ast.AnnAssign):
                if statement.value is None:
                    continue
                value = self._evaluate_expression(statement.value)
                if value is not None:
                    self._assign(statement.target, value)
            elif isinstance(statement, ast.AugAssign):
                if not isinstance(statement.op, ast.Add):
                    continue
                if not isinstance(statement.target, ast.Name):
                    continue
                left = self._environment.get(statement.target.id)
                right = self._evaluate_expression(statement.value)
                if left is not None and right is not None:
                    self._environment[statement.target.id] = left + right
            elif isinstance(statement, ast.Try):
                self._evaluate_try(statement)
            elif isinstance(statement, ast.If):
                self._evaluate_if(statement)
            elif isinstance(statement, ast.Delete):
                for target in statement.targets:
                    if isinstance(target, ast.Name):
                        self._environment.pop(target.id, None)

    def _evaluate_try(self, statement: ast.Try) -> None:
        """Prefer the try body when it resolves; otherwise use a handler."""

        original = dict(self._environment)
        self._evaluate_statements(statement.body)

        if self._environment != original:
            self._evaluate_statements(statement.orelse)
            self._evaluate_statements(statement.finalbody)
            return

        self._environment = original
        for handler in statement.handlers:
            candidate = dict(self._environment)
            self._evaluate_statements(handler.body)
            if self._environment != candidate:
                break
        self._evaluate_statements(statement.finalbody)

    def _evaluate_if(self, statement: ast.If) -> None:
        """Evaluate the branch that produces deterministic assignments.

        This is intentionally conservative. It does not attempt to determine
        arbitrary runtime truth values.
        """

        original = dict(self._environment)

        body_environment = dict(original)
        self._environment = body_environment
        self._evaluate_statements(statement.body)
        body_environment = dict(self._environment)

        self._environment = dict(original)
        self._evaluate_statements(statement.orelse)
        else_environment = dict(self._environment)

        if body_environment == else_environment:
            self._environment = body_environment
        else:
            self._environment = original
            self._findings.append(
                "Conditional public-surface assignment could not be resolved "
                "without executing code."
            )

    def _evaluate_import_from(self, statement: ast.ImportFrom) -> None:
        if self._resolver is None:
            return

        imported_module = self._absolute_import_name(
            module=statement.module,
            level=statement.level,
        )
        if not imported_module:
            return

        for alias in statement.names:
            if alias.name != "__all__":
                continue
            resolved = self._resolver(imported_module)
            if resolved is not None:
                self._environment[alias.asname or alias.name] = resolved

    def _assign(self, target: ast.expr, value: tuple[str, ...]) -> None:
        if isinstance(target, ast.Name):
            self._environment[target.id] = value

    def _evaluate_expression(
        self,
        expression: ast.expr,
    ) -> tuple[str, ...] | None:
        if isinstance(expression, ast.Constant):
            if isinstance(expression.value, str):
                return (expression.value,)
            return None

        if isinstance(expression, ast.Name):
            return self._environment.get(expression.id)

        if isinstance(expression, ast.Starred):
            return self._evaluate_expression(expression.value)

        if isinstance(expression, (ast.List, ast.Tuple, ast.Set)):
            values: list[str] = []
            for item in expression.elts:
                evaluated = self._evaluate_expression(item)
                if evaluated is None:
                    return None
                values.extend(evaluated)
            return tuple(values)

        if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
            left = self._evaluate_expression(expression.left)
            right = self._evaluate_expression(expression.right)
            if left is None or right is None:
                return None
            return left + right

        if isinstance(expression, ast.Call):
            return self._evaluate_call(expression)

        return None

    def _evaluate_call(self, expression: ast.Call) -> tuple[str, ...] | None:
        if expression.keywords:
            return None

        if isinstance(expression.func, ast.Name):
            if expression.func.id not in {"tuple", "list", "set"}:
                return None
            if not expression.args:
                return ()
            if len(expression.args) != 1:
                return None
            return self._evaluate_expression(expression.args[0])

        if (
            isinstance(expression.func, ast.Attribute)
            and isinstance(expression.func.value, ast.Name)
            and expression.func.value.id == "dict"
            and expression.func.attr == "fromkeys"
        ):
            if not expression.args:
                return ()
            if len(expression.args) > 2:
                return None
            values = self._evaluate_expression(expression.args[0])
            if values is None:
                return None
            return self._deduplicate(values)

        return None

    def _absolute_import_name(
        self,
        *,
        module: str | None,
        level: int,
    ) -> str:
        if level == 0:
            return module or ""

        parts = self._module_name.split(".")
        package_parts = parts if self._is_package else parts[:-1]
        ascend = max(level - 1, 0)

        if ascend > len(package_parts):
            return ""

        base = package_parts[: len(package_parts) - ascend]
        suffix = module.split(".") if module else []
        return ".".join((*base, *suffix))

    @staticmethod
    def _deduplicate(values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(values))


def evaluate_public_surface(
    tree: ast.Module,
    *,
    module_name: str,
    is_package: bool,
    imported_all_resolver: ImportedAllResolver | None = None,
) -> PublicSurfaceResult:
    """Convenience function for deterministic public-surface evaluation."""

    return StaticPublicSurfaceEvaluator(
        module_name=module_name,
        is_package=is_package,
        imported_all_resolver=imported_all_resolver,
    ).evaluate(tree)


__all__ = [
    "ImportedAllResolver",
    "PublicSurfaceResult",
    "StaticPublicSurfaceEvaluator",
    "evaluate_public_surface",
]
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
PYEOF

cat > tests/test_genesis_5e1c_static_public_surface.py <<'PYEOF'
from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

from core.engineering import inventory_package, inventory_target
from core.engineering.public_surface import evaluate_public_surface


class StaticPublicSurfaceTests(unittest.TestCase):
    def _evaluate(self, source: str) -> tuple[str, ...]:
        result = evaluate_public_surface(
            ast.parse(source),
            module_name="core.fixture",
            is_package=True,
        )
        self.assertTrue(result.resolved, result.findings)
        return result.symbols

    def test_literal_list(self) -> None:
        self.assertEqual(
            self._evaluate('__all__ = ["A", "B"]\n'),
            ("A", "B"),
        )

    def test_tuple_and_concatenation(self) -> None:
        self.assertEqual(
            self._evaluate(
                'base = ("A",)\n'
                '__all__ = base + ("B", "C")\n'
            ),
            ("A", "B", "C"),
        )

    def test_managed_export_pattern(self) -> None:
        source = """
__all__ = ["Existing"]

try:
    _existing_all = tuple(__all__)
except NameError:
    _existing_all = ()

__all__ = tuple(
    dict.fromkeys(
        (*_existing_all, "Assumption", "WorkspaceStatus", "Assumption")
    )
)
del _existing_all
"""
        self.assertEqual(
            self._evaluate(source),
            ("Existing", "Assumption", "WorkspaceStatus"),
        )

    def test_inventory_recognizes_managed_package_exports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "core" / "fixture"
            package.mkdir(parents=True)
            (root / "core" / "__init__.py").write_text("", encoding="utf-8")
            (package / "__init__.py").write_text(
                """
from .models import Existing
__all__ = ["Existing"]
_existing_all = tuple(__all__)
from .models import Added
__all__ = tuple(dict.fromkeys((*_existing_all, "Added")))
del _existing_all
""",
                encoding="utf-8",
            )
            (package / "models.py").write_text(
                "class Existing: pass\nclass Added: pass\n",
                encoding="utf-8",
            )

            inventory = inventory_package(root, "core.fixture")
            exported = tuple(item.symbol for item in inventory.exported_symbols)
            self.assertEqual(exported, ("Added", "Existing"))

    def test_compatibility_module_imports_upstream_all(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "core" / "fixture"
            package.mkdir(parents=True)
            (root / "core" / "__init__.py").write_text("", encoding="utf-8")
            (package / "__init__.py").write_text("", encoding="utf-8")
            (package / "object_model.py").write_text(
                """
class CognitiveObject:
    pass

__all__ = ["CognitiveObject"]
""",
                encoding="utf-8",
            )
            (package / "compatibility.py").write_text(
                """
from .object_model import *
from .object_model import __all__ as __all__
""",
                encoding="utf-8",
            )

            inventory = inventory_target(
                root,
                "core.fixture.compatibility",
            )
            exported = tuple(item.symbol for item in inventory.exported_symbols)
            self.assertEqual(exported, ("CognitiveObject",))


if __name__ == "__main__":
    unittest.main()
PYEOF

cat > dev/verification/verify_genesis_5e1c_static_public_surface.py <<'PYEOF'
#!/usr/bin/env python3
"""Verify Genesis V-E1C Static Public Surface Engine."""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check(condition: bool, label: str) -> int:
    print(f"[{'PASS' if condition else 'FAIL'}] {label}")
    return 0 if condition else 1


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = (
        f"{ROOT}{os.pathsep}{environment['PYTHONPATH']}"
        if environment.get("PYTHONPATH")
        else str(ROOT)
    )
    environment["PYTHON_BIN"] = sys.executable
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        text=True,
    )


def forbidden_authority(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    forbidden = {
        "subprocess",
        "socket",
        "requests",
        "urllib",
        "httpx",
        "importlib",
    }
    findings: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in forbidden:
                    findings.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.split(".")[0] in forbidden:
                findings.add(module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                findings.add(node.func.id)

    return tuple(sorted(findings))


def main() -> int:
    failures = 0

    required = (
        ROOT / "core/engineering/public_surface.py",
        ROOT / "core/engineering/api_inventory.py",
        ROOT / "tests/test_genesis_5e1c_static_public_surface.py",
        ROOT / "docs/engineering/genesis_v_e1c_static_public_surface.md",
    )
    failures += check(
        all(path.is_file() for path in required),
        "V-E1C required files",
    )

    compile_result = run(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            "core/engineering/public_surface.py",
            "core/engineering/api_inventory.py",
            "tests/test_genesis_5e1c_static_public_surface.py",
            "dev/verification/verify_genesis_5e1c_static_public_surface.py",
        ]
    )
    failures += check(
        compile_result.returncode == 0,
        "V-E1C compilation",
    )

    authority_findings = forbidden_authority(
        ROOT / "core/engineering/public_surface.py"
    )
    failures += check(
        not authority_findings,
        "Static evaluator has no runtime import, process, or network authority",
    )

    tests_result = run(
        [
            sys.executable,
            "-m",
            "unittest",
            "-v",
            "tests.test_genesis_5e1c_static_public_surface",
        ]
    )
    failures += check(
        tests_result.returncode == 0,
        "V-E1C unit tests",
    )

    analyzer_result = run(
        [
            "bash",
            "dev/analyze_public_api_compatibility.sh",
        ]
    )
    failures += check(
        analyzer_result.returncode == 0,
        "Compatibility analyzer execution",
    )

    evidence_path = (
        ROOT
        / ".artifacts"
        / "engineering"
        / "public_api_compatibility.json"
    )
    evidence_exists = evidence_path.is_file()
    failures += check(
        evidence_exists,
        "Compatibility JSON evidence",
    )

    findings: list[dict[str, object]] = []
    score = 0.0
    if evidence_exists:
        payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        findings = list(payload.get("findings", ()))
        score = float(payload.get("compatibility_score", 0.0))

    cognition_findings = [
        finding
        for finding in findings
        if str(finding.get("package", "")).startswith("core.cognition")
    ]
    failures += check(
        not cognition_findings,
        "Cognition compatibility findings eliminated",
    )

    failures += check(
        score == 1.0,
        "Public API compatibility score is 100%",
    )

    ve1_result = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_5e1_public_api_compatibility.py",
        ]
    )
    failures += check(
        ve1_result.returncode == 0,
        "Genesis V-E1 regression",
    )

    ve1a_result = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_5e1a_repository_reality_modeling.py",
        ]
    )
    failures += check(
        ve1a_result.returncode == 0,
        "Genesis V-E1A regression",
    )

    ve1b_result = run(
        [
            sys.executable,
            "dev/verification/verify_genesis_5e1b_cognition_api_restoration.py",
        ]
    )
    failures += check(
        ve1b_result.returncode == 0,
        "Genesis V-E1B regression",
    )

    print()
    print("-" * 72)
    print(f"Checks failed : {failures}")
    print(
        "Overall status: "
        f"{'EXCELLENT' if failures == 0 else 'FAILED'}"
    )
    print("=" * 72)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
PYEOF

cat > dev/verify_genesis_5e1c.sh <<'BASHEOF'
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python}"

cd "${PROJECT_ROOT}"

echo
echo "========================================================================"
echo "JARVIS GENESIS V-E1C — STATIC PUBLIC SURFACE ENGINE"
echo "========================================================================"

"${PYTHON_BIN}" \
    dev/verification/verify_genesis_5e1c_static_public_surface.py
BASHEOF

cat > docs/engineering/genesis_v_e1c_static_public_surface.md <<'MDEOF'
# Genesis V-E1C — Static Public Surface Engine

## Status

Implemented.

## Mission

Provide one deterministic, non-executing authority for reconstructing Python
package and module public API surfaces.

## Supported Forms

The evaluator supports:

- list, tuple, and set literals;
- starred collection expansion;
- sequence concatenation;
- `tuple(...)`, `list(...)`, and `set(...)`;
- `dict.fromkeys(...)` deduplication;
- prior variable assignments;
- prior `__all__` assignments;
- managed compatibility export blocks;
- imported `__all__` aliases from repository-local modules;
- compatibility modules that re-export an upstream public surface.

## Engineering Boundary

The evaluator:

- parses source with `ast`;
- does not import repository modules;
- does not call `eval` or `exec`;
- does not start processes;
- does not use network access;
- does not modify analyzed source.

## Certification Target

Genesis V-E1C is certified when:

1. the fourteen restored `core.cognition` exports are statically recognized;
2. `core.cognition.common.cognitive_object.CognitiveObject` is recognized
   through its compatibility-module `__all__` alias;
3. the public API compatibility report reaches 100 percent;
4. Genesis V-E1, V-E1A, and V-E1B regressions remain excellent.
MDEOF

chmod +x \
    dev/verify_genesis_5e1c.sh \
    dev/verification/verify_genesis_5e1c_static_public_surface.py

echo
echo "[PASS] Static Public Surface Engine installed"
echo "[PASS] api_inventory.py replaced with canonical evaluator integration"
echo "[PASS] V-E1C tests and verification installed"
echo "[PASS] Backup: .migration_backups/genesis_5e1c/${timestamp}_api_inventory.py"
echo

PYTHON_BIN="${PYTHON_BIN}" ./dev/verify_genesis_5e1c.sh
