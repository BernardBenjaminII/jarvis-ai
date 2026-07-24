"""
Phase VII-A8 acquisition integration-freeze verification.

This suite freezes the completed VII-A subsystem before provider expansion.

It verifies:

- complete production-module importability
- canonical package structure
- deterministic dependency direction
- no lower-layer imports of higher layers
- Phase VI dependency isolation
- stable public exports
- removal of the obsolete dispatcher package
- deterministic architecture fingerprint

No live catalog, acquisition database, network, or source content is modified.
"""

from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

from knowledge_engine.acquisition.contracts import (
    ACQUISITION_LAYER_INDEX,
    ACQUISITION_LAYER_ORDER,
    ACQUISITION_PUBLIC_MODULES,
    EXPECTED_PUBLIC_SYMBOLS,
    PHASE_VI_IMPORT_ALLOWLIST,
    build_acquisition_contract_snapshot,
)


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

ACQUISITION_ROOT = (
    REPO_ROOT
    / "knowledge_engine"
    / "acquisition"
)


def module_name_for_path(
    path: Path,
) -> str:
    """Convert one repository Python path into an import name."""

    relative = path.relative_to(
        REPO_ROOT
    )

    parts = list(
        relative.with_suffix("").parts
    )

    if parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def discover_python_files() -> tuple[Path, ...]:
    """Return all acquisition production Python files."""

    return tuple(
        sorted(
            path
            for path in ACQUISITION_ROOT.rglob(
                "*.py"
            )
            if "__pycache__" not in path.parts
        )
    )


def discover_importable_modules(
) -> tuple[str, ...]:
    """Discover all importable acquisition modules."""

    package = importlib.import_module(
        "knowledge_engine.acquisition"
    )

    discovered = {
        "knowledge_engine.acquisition"
    }

    for item in pkgutil.walk_packages(
        package.__path__,
        prefix=(
            "knowledge_engine.acquisition."
        ),
    ):
        discovered.add(item.name)

    return tuple(sorted(discovered))


def imports_for_path(
    path: Path,
) -> tuple[str, ...]:
    """Return all imported module paths from one Python source file."""

    tree = ast.parse(
        path.read_text(encoding="utf-8"),
        filename=str(path),
    )

    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name
                for alias in node.names
            )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    return tuple(sorted(imports))


def acquisition_layer(
    module_name: str,
) -> str | None:
    """Return the acquisition layer represented by a module name."""

    prefix = (
        "knowledge_engine.acquisition."
    )

    if not module_name.startswith(prefix):
        return None

    remainder = module_name[
        len(prefix):
    ]

    layer_name = remainder.split(
        ".",
        1,
    )[0]

    if layer_name not in (
        ACQUISITION_LAYER_INDEX
    ):
        return None

    return layer_name


def verify_package_root_exists() -> None:
    assert ACQUISITION_ROOT.is_dir()

    for layer_name in (
        ACQUISITION_LAYER_ORDER
    ):
        layer_path = (
            ACQUISITION_ROOT
            / layer_name
        )

        assert layer_path.is_dir(), (
            f"Missing acquisition layer: "
            f"{layer_name}"
        )

        assert (
            layer_path / "__init__.py"
        ).is_file(), (
            f"Missing package initializer: "
            f"{layer_name}"
        )


def verify_obsolete_dispatcher_absent() -> None:
    obsolete = (
        ACQUISITION_ROOT
        / "dispatcher"
    )

    assert not obsolete.exists(), (
        "Obsolete acquisition/dispatcher "
        "package must not return"
    )


def verify_all_modules_import() -> None:
    modules = discover_importable_modules()

    failures: list[str] = []

    for module_name in modules:
        try:
            importlib.import_module(
                module_name
            )
        except Exception as exc:
            failures.append(
                f"{module_name}: "
                f"{type(exc).__name__}: {exc}"
            )

    assert not failures, (
        "Acquisition import failures:\n"
        + "\n".join(failures)
    )

    assert len(modules) >= 20


def verify_public_modules() -> None:
    for module_name in (
        ACQUISITION_PUBLIC_MODULES
    ):
        module = importlib.import_module(
            module_name
        )

        assert isinstance(
            module,
            ModuleType,
        )

        exports = tuple(
            getattr(
                module,
                "__all__",
                (),
            )
        )

        expected = (
            EXPECTED_PUBLIC_SYMBOLS[
                module_name
            ]
        )

        for symbol_name in expected:
            assert hasattr(
                module,
                symbol_name,
            ), (
                f"{module_name} does not expose "
                f"{symbol_name}"
            )

            assert symbol_name in exports, (
                f"{module_name}.__all__ omits "
                f"{symbol_name}"
            )


def verify_forward_dependency_direction() -> None:
    """
    Ensure earlier acquisition layers do not import later layers.

    Allowed direction:

        admission
            ↓
        provenance
            ↓
        intake
            ↓
        missions
            ↓
        handoff
            ↓
        dispatch

    Later layers may import earlier layers.
    Earlier layers may not import later layers.
    """

    violations: list[str] = []

    for path in discover_python_files():
        source_module = (
            module_name_for_path(path)
        )

        source_layer = acquisition_layer(
            source_module
        )

        if source_layer is None:
            continue

        source_index = (
            ACQUISITION_LAYER_INDEX[
                source_layer
            ]
        )

        for imported in imports_for_path(
            path
        ):
            imported_layer = (
                acquisition_layer(
                    imported
                )
            )

            if imported_layer is None:
                continue

            imported_index = (
                ACQUISITION_LAYER_INDEX[
                    imported_layer
                ]
            )

            if imported_index > source_index:
                violations.append(
                    f"{source_module} imports "
                    f"later layer {imported}"
                )

    assert not violations, (
        "Acquisition dependency-direction "
        "violations:\n"
        + "\n".join(violations)
    )


def verify_phase_vi_import_isolation() -> None:
    """
    Ensure only the narrow dispatch adapter imports Phase VI.

    Acquisition implementation modules must not depend directly on:

    - assimilation handlers
    - assimilation services
    - assimilation mission storage
    - assimilation SQL ownership
    - extraction or persistence internals
    """

    violations: list[str] = []

    assimilation_prefix = (
        "knowledge_engine.assimilation"
    )

    for path in discover_python_files():
        source_module = (
            module_name_for_path(path)
        )

        assimilation_imports = tuple(
            imported
            for imported in imports_for_path(
                path
            )
            if imported.startswith(
                assimilation_prefix
            )
        )

        if not assimilation_imports:
            continue

        if source_module not in (
            PHASE_VI_IMPORT_ALLOWLIST
        ):
            for imported in (
                assimilation_imports
            ):
                violations.append(
                    f"{source_module} imports "
                    f"{imported}"
                )

            continue

        assert assimilation_imports == (
            "knowledge_engine.assimilation.runner",
        ), (
            "The Phase VI adapter may import only "
            "AssimilationRunner"
        )

    assert not violations, (
        "Unauthorized Phase VI imports:\n"
        + "\n".join(violations)
    )


def verify_no_development_dependencies() -> None:
    forbidden_prefixes = (
        "dev",
        "tests",
    )

    violations: list[str] = []

    for path in discover_python_files():
        source_module = (
            module_name_for_path(path)
        )

        for imported in imports_for_path(
            path
        ):
            if imported.startswith(
                forbidden_prefixes
            ):
                violations.append(
                    f"{source_module} imports "
                    f"{imported}"
                )

    assert not violations, (
        "Production acquisition code imports "
        "development code:\n"
        + "\n".join(violations)
    )


def verify_no_duplicate_module_names() -> None:
    module_names = tuple(
        module_name_for_path(path)
        for path in discover_python_files()
    )

    assert len(module_names) == len(
        set(module_names)
    )


def verify_contract_snapshot() -> None:
    first = (
        build_acquisition_contract_snapshot()
    )

    second = (
        build_acquisition_contract_snapshot()
    )

    assert first == second
    assert first.fingerprint == (
        second.fingerprint
    )

    assert len(first.fingerprint) == 64

    int(
        first.fingerprint,
        16,
    )

    payload = first.to_dict()

    assert payload["layers"] == list(
        ACQUISITION_LAYER_ORDER
    )

    assert payload["public_modules"] == list(
        ACQUISITION_PUBLIC_MODULES
    )


def verify_contract_immutability() -> None:
    snapshot = (
        build_acquisition_contract_snapshot()
    )

    try:
        snapshot.fingerprint = "changed"  # type: ignore[misc]
    except (
        AttributeError,
        TypeError,
    ):
        pass
    else:
        raise AssertionError(
            "Acquisition contract snapshot "
            "must remain immutable"
        )


def main() -> None:
    verify_package_root_exists()
    verify_obsolete_dispatcher_absent()
    verify_all_modules_import()
    verify_public_modules()
    verify_forward_dependency_direction()
    verify_phase_vi_import_isolation()
    verify_no_development_dependencies()
    verify_no_duplicate_module_names()
    verify_contract_snapshot()
    verify_contract_immutability()

    print("[PASS] Canonical acquisition package structure")
    print("[PASS] Obsolete dispatcher package absent")
    print("[PASS] Complete acquisition module importability")
    print("[PASS] Stable public acquisition exports")
    print("[PASS] Forward-only layer dependencies")
    print("[PASS] Phase VI import isolation")
    print("[PASS] Production/development dependency separation")
    print("[PASS] Unique acquisition module identities")
    print("[PASS] Deterministic architecture fingerprint")
    print("[PASS] Immutable architecture snapshot")
    print("----------------------------------------------------------------------")
    print("[PASS] Acquisition integration freeze tests completed")


if __name__ == "__main__":
    main()
