"""
JARVIS Gen 2 Phase VII-A7 interface audit.

This read-only audit identifies the canonical Phase VI assimilation entry
points that Phase VII-A7 must use.

It performs no database writes, file mutation, mission creation, assimilation,
or network access.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import json
import pkgutil
from dataclasses import asdict, dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]

ASSIMILATION_ROOT = (
    REPO_ROOT
    / "knowledge_engine"
    / "assimilation"
)

OUTPUT_PATH = (
    REPO_ROOT
    / "artifacts"
    / "phase_vii"
    / "phase_7a7_interface_audit.json"
)

TARGET_MODULES = (
    "knowledge_engine.assimilation",
    "knowledge_engine.assimilation.director",
    "knowledge_engine.assimilation.runner",
    "knowledge_engine.assimilation.mission",
    "knowledge_engine.assimilation.mission_store",
    "knowledge_engine.assimilation.planner",
    "knowledge_engine.assimilation.dispatch",
    "knowledge_engine.assimilation.registry_builder",
    "knowledge_engine.assimilation.single_document",
    "knowledge_engine.assimilation.services",
)


@dataclass(frozen=True)
class CallableContract:
    """Serializable callable signature."""

    module: str
    owner: str | None
    name: str
    signature: str
    kind: str
    docstring: str | None


@dataclass(frozen=True)
class ClassContract:
    """Serializable public class contract."""

    module: str
    name: str
    constructor_signature: str
    bases: tuple[str, ...]
    methods: tuple[CallableContract, ...]
    docstring: str | None


@dataclass(frozen=True)
class ModuleContract:
    """Serializable module inventory."""

    module: str
    file: str | None
    imported: bool
    import_error: str | None
    classes: tuple[ClassContract, ...]
    functions: tuple[CallableContract, ...]
    exports: tuple[str, ...]


@dataclass(frozen=True)
class SourceFileContract:
    """Static source-file inventory."""

    path: str
    classes: tuple[str, ...]
    functions: tuple[str, ...]
    imports: tuple[str, ...]
    sql_tokens: tuple[str, ...]


def safe_signature(value: Any) -> str:
    """Return a signature without allowing inspection failure to abort."""

    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return "<signature unavailable>"


def short_docstring(value: Any) -> str | None:
    """Return the first nonblank documentation line."""

    text = inspect.getdoc(value)

    if not text:
        return None

    for line in text.splitlines():
        normalized = line.strip()

        if normalized:
            return normalized

    return None


def public_methods(
    *,
    module_name: str,
    cls: type[Any],
) -> tuple[CallableContract, ...]:
    """Inspect public methods defined directly by a class."""

    methods: list[CallableContract] = []

    for name, raw_value in cls.__dict__.items():
        if name.startswith("_"):
            continue

        value = raw_value

        if isinstance(raw_value, staticmethod):
            value = raw_value.__func__
            kind = "staticmethod"
        elif isinstance(raw_value, classmethod):
            value = raw_value.__func__
            kind = "classmethod"
        elif inspect.isfunction(raw_value):
            kind = "method"
        elif isinstance(raw_value, property):
            kind = "property"

            methods.append(
                CallableContract(
                    module=module_name,
                    owner=cls.__name__,
                    name=name,
                    signature="<property>",
                    kind=kind,
                    docstring=short_docstring(
                        raw_value.fget
                    ),
                )
            )

            continue
        else:
            continue

        methods.append(
            CallableContract(
                module=module_name,
                owner=cls.__name__,
                name=name,
                signature=safe_signature(value),
                kind=kind,
                docstring=short_docstring(value),
            )
        )

    return tuple(
        sorted(
            methods,
            key=lambda contract: contract.name,
        )
    )


def inspect_module(
    module_name: str,
) -> ModuleContract:
    """Import and inventory one target module."""

    try:
        module = importlib.import_module(
            module_name
        )
    except Exception as exc:
        return ModuleContract(
            module=module_name,
            file=None,
            imported=False,
            import_error=(
                f"{type(exc).__name__}: {exc}"
            ),
            classes=(),
            functions=(),
            exports=(),
        )

    classes: list[ClassContract] = []
    functions: list[CallableContract] = []

    for name, value in vars(module).items():
        if name.startswith("_"):
            continue

        if inspect.isclass(value):
            if value.__module__ != module.__name__:
                continue

            classes.append(
                ClassContract(
                    module=module.__name__,
                    name=value.__name__,
                    constructor_signature=(
                        safe_signature(value)
                    ),
                    bases=tuple(
                        base.__name__
                        for base in value.__bases__
                    ),
                    methods=public_methods(
                        module_name=module.__name__,
                        cls=value,
                    ),
                    docstring=short_docstring(value),
                )
            )

        elif inspect.isfunction(value):
            if value.__module__ != module.__name__:
                continue

            functions.append(
                CallableContract(
                    module=module.__name__,
                    owner=None,
                    name=name,
                    signature=safe_signature(value),
                    kind="function",
                    docstring=short_docstring(value),
                )
            )

    exports_value = getattr(
        module,
        "__all__",
        (),
    )

    exports = tuple(
        str(item)
        for item in exports_value
    )

    return ModuleContract(
        module=module.__name__,
        file=getattr(
            module,
            "__file__",
            None,
        ),
        imported=True,
        import_error=None,
        classes=tuple(
            sorted(
                classes,
                key=lambda contract: contract.name,
            )
        ),
        functions=tuple(
            sorted(
                functions,
                key=lambda contract: contract.name,
            )
        ),
        exports=exports,
    )


def discover_assimilation_modules() -> tuple[str, ...]:
    """Discover all importable assimilation package modules."""

    package = importlib.import_module(
        "knowledge_engine.assimilation"
    )

    package_path = getattr(
        package,
        "__path__",
        None,
    )

    discovered = set(TARGET_MODULES)

    if package_path is not None:
        for item in pkgutil.walk_packages(
            package_path,
            prefix=(
                "knowledge_engine."
                "assimilation."
            ),
        ):
            discovered.add(item.name)

    return tuple(sorted(discovered))


def static_source_contract(
    path: Path,
) -> SourceFileContract:
    """Inspect imports, definitions, and SQL ownership statically."""

    text = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        text,
        filename=str(path),
    )

    classes: list[str] = []
    functions: list[str] = []
    imports: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            functions.append(node.name)

        elif isinstance(node, ast.Import):
            imports.extend(
                alias.name
                for alias in node.names
            )

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            imports.extend(
                f"{module}.{alias.name}"
                for alias in node.names
            )

    sql_tokens = tuple(
        token
        for token in (
            "SELECT ",
            "INSERT ",
            "UPDATE ",
            "DELETE ",
            "CREATE TABLE",
        )
        if token in text.upper()
    )

    return SourceFileContract(
        path=str(
            path.relative_to(REPO_ROOT)
        ),
        classes=tuple(sorted(set(classes))),
        functions=tuple(
            sorted(set(functions))
        ),
        imports=tuple(sorted(set(imports))),
        sql_tokens=sql_tokens,
    )


def inspect_source_tree(
) -> tuple[SourceFileContract, ...]:
    """Inspect all assimilation Python files statically."""

    if not ASSIMILATION_ROOT.exists():
        raise RuntimeError(
            "Assimilation package directory was not found"
        )

    contracts = tuple(
        static_source_contract(path)
        for path in sorted(
            ASSIMILATION_ROOT.rglob("*.py")
        )
    )

    return contracts


def find_candidate_entry_points(
    modules: tuple[ModuleContract, ...],
) -> tuple[dict[str, Any], ...]:
    """
    Extract likely composition and execution entry points.

    This does not decide which API VII-A7 will use. It highlights the
    candidates for review.
    """

    keywords = (
        "build",
        "create",
        "dispatch",
        "execute",
        "process",
        "resume",
        "run",
        "submit",
    )

    candidates: list[dict[str, Any]] = []

    for module in modules:
        for function in module.functions:
            if any(
                keyword in function.name.lower()
                for keyword in keywords
            ):
                candidates.append(
                    asdict(function)
                )

        for class_contract in module.classes:
            for method in class_contract.methods:
                if any(
                    keyword in method.name.lower()
                    for keyword in keywords
                ):
                    candidates.append(
                        asdict(method)
                    )

    return tuple(
        sorted(
            candidates,
            key=lambda item: (
                item["module"],
                item["owner"] or "",
                item["name"],
            ),
        )
    )


def write_report(
    *,
    modules: tuple[ModuleContract, ...],
    sources: tuple[SourceFileContract, ...],
) -> None:
    """Write deterministic JSON audit output."""

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "repository_root": str(REPO_ROOT),
        "assimilation_root": str(
            ASSIMILATION_ROOT
        ),
        "modules": [
            asdict(module)
            for module in modules
        ],
        "source_files": [
            asdict(source)
            for source in sources
        ],
        "candidate_entry_points": list(
            find_candidate_entry_points(
                modules
            )
        ),
    }

    OUTPUT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def print_summary(
    *,
    modules: tuple[ModuleContract, ...],
    sources: tuple[SourceFileContract, ...],
) -> None:
    """Print a concise human-readable audit summary."""

    imported = tuple(
        module
        for module in modules
        if module.imported
    )

    failures = tuple(
        module
        for module in modules
        if not module.imported
    )

    entry_points = find_candidate_entry_points(
        modules
    )

    print(
        "============================================================"
    )
    print(
        "JARVIS GEN 2 — PHASE VII-A7 INTERFACE AUDIT"
    )
    print(
        "============================================================"
    )

    print(
        f"Modules discovered : {len(modules)}"
    )
    print(
        f"Modules imported   : {len(imported)}"
    )
    print(
        f"Import failures    : {len(failures)}"
    )
    print(
        f"Source files       : {len(sources)}"
    )
    print(
        f"Entry candidates   : {len(entry_points)}"
    )
    print()

    print("LIKELY CANONICAL ENTRY POINTS")
    print(
        "------------------------------------------------------------"
    )

    for item in entry_points:
        owner = (
            f"{item['owner']}."
            if item["owner"]
            else ""
        )

        print(
            f"{item['module']}: "
            f"{owner}{item['name']}"
            f"{item['signature']}"
        )

    if failures:
        print()
        print("IMPORT FAILURES")
        print(
            "------------------------------------------------------------"
        )

        for module in failures:
            print(
                f"{module.module}: "
                f"{module.import_error}"
            )

    print()
    print(f"JSON report: {OUTPUT_PATH}")
    print(
        "============================================================"
    )


def main() -> None:
    module_names = (
        discover_assimilation_modules()
    )

    modules = tuple(
        inspect_module(module_name)
        for module_name in module_names
    )

    sources = inspect_source_tree()

    write_report(
        modules=modules,
        sources=sources,
    )

    print_summary(
        modules=modules,
        sources=sources,
    )


if __name__ == "__main__":
    main()
