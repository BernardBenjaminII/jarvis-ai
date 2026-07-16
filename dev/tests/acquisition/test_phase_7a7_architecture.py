"""
Architecture verification for Phase VII-A7.

This suite verifies the dispatcher layer remains a pure orchestration
boundary.

It must never:

    • perform extraction
    • access Phase VI SQL
    • import handler implementations
    • perform chunking
    • perform embeddings
    • access registry persistence directly

Instead it must communicate exclusively through explicit ports.
"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[3]
)

DISPATCH = (
    ROOT
    / "knowledge_engine"
    / "acquisition"
    / "dispatch"
)


SERVICE = DISPATCH / "service.py"
REPOSITORY = DISPATCH / "repository.py"
PHASE_VI = DISPATCH / "phase_vi.py"
PORTS = DISPATCH / "ports.py"


# ---------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------


def parse(path: Path) -> ast.Module:
    return ast.parse(
        path.read_text(
            encoding="utf-8"
        )
    )


def imported_modules(
    module: ast.Module,
) -> set[str]:

    imports: set[str] = set()

    for node in ast.walk(module):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.add(node.module)

    return imports


def imported_names(
    module: ast.Module,
) -> set[str]:

    names: set[str] = set()

    for node in ast.walk(module):

        if isinstance(node, ast.Import):

            for alias in node.names:
                names.add(alias.name)

        elif isinstance(node, ast.ImportFrom):

            for alias in node.names:
                names.add(alias.name)

    return names


# ---------------------------------------------------------------------
# existence
# ---------------------------------------------------------------------


def verify_files_exist():

    assert SERVICE.exists()

    assert REPOSITORY.exists()

    assert PHASE_VI.exists()

    assert PORTS.exists()

    print("[PASS] Dispatch package complete")


# ---------------------------------------------------------------------
# repository ownership
# ---------------------------------------------------------------------


def verify_repository_has_no_phase_vi_imports():

    imports = imported_modules(
        parse(REPOSITORY)
    )

    forbidden = (
        "knowledge_engine.assimilation",
        "knowledge_engine.processing",
        "knowledge_engine.chunking",
        "knowledge_engine.embeddings",
    )

    for module in imports:

        for prefix in forbidden:

            assert not module.startswith(
                prefix
            ), (
                "Dispatch repository imports "
                f"forbidden module {module}"
            )

    print("[PASS] Repository ownership")


# ---------------------------------------------------------------------
# service ownership
# ---------------------------------------------------------------------


def verify_service_has_no_sql():

    text = SERVICE.read_text()

    forbidden = (
        "SELECT ",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
        "CREATE TABLE",
        "sqlite3.connect",
    )

    for token in forbidden:

        assert token not in text

    print("[PASS] Service contains no SQL")


# ---------------------------------------------------------------------
# service imports
# ---------------------------------------------------------------------


def verify_service_uses_ports():

    imports = imported_modules(
        parse(SERVICE)
    )

    assert (
        "knowledge_engine.acquisition.dispatch.ports"
        in imports
    )

    print("[PASS] Dispatcher uses explicit ports")


# ---------------------------------------------------------------------
# handler isolation
# ---------------------------------------------------------------------


def verify_no_handler_imports():

    imports = imported_modules(
        parse(SERVICE)
    )

    forbidden = (
        "knowledge_engine.assimilation.handlers",
        "knowledge_engine.assimilation.runner",
        "knowledge_engine.processing",
        "knowledge_engine.chunking",
        "knowledge_engine.embeddings",
        "knowledge_engine.services",
    )

    for module in imports:

        for prefix in forbidden:

            assert not module.startswith(
                prefix
            )

    print("[PASS] No handler imports")


# ---------------------------------------------------------------------
# phase vi adapter
# ---------------------------------------------------------------------


def verify_phase_vi_isolated():

    imports = imported_modules(
        parse(PHASE_VI)
    )

    assert (
        "knowledge_engine.assimilation.runner"
        in imports
    )

    forbidden = (
        "knowledge_engine.storage",
        "knowledge_engine.chunking",
        "knowledge_engine.embeddings",
        "knowledge_engine.processing",
    )

    for module in imports:

        for prefix in forbidden:

            assert not module.startswith(
                prefix
            )

    print("[PASS] Phase VI adapter isolation")


# ---------------------------------------------------------------------
# port definitions
# ---------------------------------------------------------------------


def verify_ports_are_protocols():

    names = imported_names(
        parse(PORTS)
    )

    assert "Protocol" in names

    print("[PASS] Explicit protocol ports")


# ---------------------------------------------------------------------
# public api
# ---------------------------------------------------------------------


def verify_public_symbols():

    namespace = {}

    exec(
        PORTS.read_text(),
        namespace,
    )

    exec(
        SERVICE.read_text(),
        namespace,
    )

    assert (
        "AcquisitionRegistrationPort"
        in namespace
    )

    assert (
        "PhaseVIExecutionPort"
        in namespace
    )

    assert (
        "CanonicalAssimilationDispatcher"
        in namespace
    )

    print("[PASS] Public API")


# ---------------------------------------------------------------------
# layering
# ---------------------------------------------------------------------


def verify_layering():

    service_imports = imported_modules(
        parse(SERVICE)
    )

    repository_imports = imported_modules(
        parse(REPOSITORY)
    )

    assert (
        "knowledge_engine.acquisition.dispatch.repository"
        in service_imports
    )

    assert (
        "knowledge_engine.acquisition.dispatch.service"
        not in repository_imports
    )

    print("[PASS] One-way dependency graph")


# ---------------------------------------------------------------------
# main
# ---------------------------------------------------------------------


def main():

    verify_files_exist()

    verify_repository_has_no_phase_vi_imports()

    verify_service_has_no_sql()

    verify_service_uses_ports()

    verify_no_handler_imports()

    verify_phase_vi_isolated()

    verify_ports_are_protocols()

    verify_public_symbols()

    verify_layering()

    print("------------------------------------------------------------")
    print("[PASS] Phase VII-A7 architecture verified")


if __name__ == "__main__":
    main()
