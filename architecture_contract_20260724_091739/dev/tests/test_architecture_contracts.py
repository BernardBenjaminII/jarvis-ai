"""
JARVIS Gen 2 assimilation architecture-contract verification.

These tests protect architectural boundaries rather than runtime behavior.

Protected rules:

1. Assimilation services must not import the Runner or Director.
2. Assimilation services must remain isolated from one another.
3. Handlers must not contain SQL.
4. Handlers must not import database-storage implementations.
5. The Director must not import concrete handler implementations.
6. The Runner must not perform extraction directly.
7. The Runner must not directly write document, chunk, or attempt tables.
8. The ExtractionService must own format-aware reading and chunking.
9. The PersistenceService must own document_text and chunks SQL.
10. The AttemptJournalService must own attempt-journal SQL.
11. The StateService must own registry and queue transition SQL.
12. The registry builder is the only composition root for concrete handlers.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]

ASSIMILATION_ROOT = (
    REPO_ROOT
    / "knowledge_engine"
    / "assimilation"
)

RUNNER_PATH = ASSIMILATION_ROOT / "runner.py"
DIRECTOR_PATH = ASSIMILATION_ROOT / "director.py"
REGISTRY_BUILDER_PATH = (
    ASSIMILATION_ROOT
    / "registry_builder.py"
)

HANDLERS_ROOT = ASSIMILATION_ROOT / "handlers"
SERVICES_ROOT = ASSIMILATION_ROOT / "services"

EXTRACTION_SERVICE_PATH = SERVICES_ROOT / "extraction.py"
PERSISTENCE_SERVICE_PATH = SERVICES_ROOT / "persistence.py"
ATTEMPT_SERVICE_PATH = SERVICES_ROOT / "attempts.py"
STATE_SERVICE_PATH = SERVICES_ROOT / "state.py"

REPOSITORIES_ROOT = ASSIMILATION_ROOT / "repositories"
KNOWLEDGE_REGISTRY_REPOSITORY_PATH = (
    REPOSITORIES_ROOT / "knowledge_registry.py"
)


@dataclass(frozen=True)
class SourceFacts:
    """AST-derived architectural facts for one Python module."""

    path: Path
    imports: frozenset[str]
    calls: frozenset[str]
    string_literals: tuple[str, ...]


def relative(path: Path) -> str:
    """Return a repository-relative display path."""

    return str(path.relative_to(REPO_ROOT))


def parse_python(path: Path) -> ast.Module:
    """Parse one repository Python file."""

    assert path.exists(), (
        f"Required architecture file does not exist: {relative(path)}"
    )

    source = path.read_text(encoding="utf-8")

    try:
        return ast.parse(
            source,
            filename=relative(path),
        )
    except SyntaxError as exc:
        raise AssertionError(
            f"Syntax error while parsing {relative(path)}: {exc}"
        ) from exc


def qualified_name(node: ast.AST) -> str | None:
    """Return a dotted name for Name/Attribute AST nodes."""

    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        prefix = qualified_name(node.value)

        if prefix:
            return f"{prefix}.{node.attr}"

        return node.attr

    return None


def inspect_source(path: Path) -> SourceFacts:
    """Collect imports, function calls, and string literals."""

    tree = parse_python(path)

    imports: set[str] = set()
    calls: set[str] = set()
    strings: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.add(module)

            for alias in node.names:
                imports.add(
                    f"{module}.{alias.name}"
                    if module
                    else alias.name
                )

        elif isinstance(node, ast.Call):
            name = qualified_name(node.func)

            if name:
                calls.add(name)

        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        ):
            strings.append(node.value)

    return SourceFacts(
        path=path,
        imports=frozenset(imports),
        calls=frozenset(calls),
        string_literals=tuple(strings),
    )


def python_files(root: Path) -> list[Path]:
    """Return deterministic Python files below one directory."""

    assert root.exists(), (
        f"Required architecture directory does not exist: "
        f"{relative(root)}"
    )

    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def imported_module_matches(
    imported_module: str,
    forbidden_module: str,
) -> bool:
    """Match one module or anything below it."""

    return (
        imported_module == forbidden_module
        or imported_module.startswith(
            f"{forbidden_module}."
        )
    )


def assert_no_forbidden_imports(
    facts: SourceFacts,
    forbidden_modules: Iterable[str],
) -> None:
    """Ensure a module does not import prohibited dependencies."""

    violations: list[str] = []

    for imported in sorted(facts.imports):
        for forbidden in forbidden_modules:
            if imported_module_matches(
                imported,
                forbidden,
            ):
                violations.append(imported)

    assert not violations, (
        f"{relative(facts.path)} violates dependency direction. "
        f"Forbidden imports: {violations}"
    )


def assert_contains_import(
    facts: SourceFacts,
    required_module: str,
) -> None:
    """Ensure one expected architectural dependency exists."""

    assert any(
        imported_module_matches(
            imported,
            required_module,
        )
        for imported in facts.imports
    ), (
        f"{relative(facts.path)} must import "
        f"{required_module!r}"
    )


def assert_no_sql_tokens(
    facts: SourceFacts,
    *,
    forbidden_tokens: Iterable[str],
) -> None:
    """Ensure AST string literals do not contain forbidden SQL tokens."""

    matches: list[str] = []

    for literal in facts.string_literals:
        normalized = " ".join(
            literal.upper().split()
        )

        for token in forbidden_tokens:
            if token.upper() in normalized:
                matches.append(token)

    assert not matches, (
        f"{relative(facts.path)} contains forbidden SQL responsibility: "
        f"{sorted(set(matches))}"
    )


def assert_has_sql_tokens(
    facts: SourceFacts,
    *,
    required_tokens: Iterable[str],
) -> None:
    """Ensure an owning service contains its expected SQL tokens."""

    normalized_literals = [
        " ".join(literal.upper().split())
        for literal in facts.string_literals
    ]

    missing = [
        token
        for token in required_tokens
        if not any(
            token.upper() in literal
            for literal in normalized_literals
        )
    ]

    assert not missing, (
        f"{relative(facts.path)} is missing expected owned SQL: "
        f"{missing}"
    )


def verify_service_dependency_direction() -> None:
    """
    Services are leaf business components.

    They may depend on standard-library modules and low-level extraction
    utilities, but not on orchestration layers or sibling services.
    """

    service_modules = {
        "knowledge_engine.assimilation.services.attempts",
        "knowledge_engine.assimilation.services.extraction",
        "knowledge_engine.assimilation.services.persistence",
        "knowledge_engine.assimilation.services.state",
    }

    orchestration_modules = {
        "knowledge_engine.assimilation.director",
        "knowledge_engine.assimilation.runner",
        "knowledge_engine.assimilation.registry_builder",
        "knowledge_engine.assimilation.handler_registry",
        "knowledge_engine.assimilation.handlers",
    }

    for path in python_files(SERVICES_ROOT):
        if path.name == "__init__.py":
            # The package export file intentionally imports sibling services.
            continue

        facts = inspect_source(path)

        current_module = (
            "knowledge_engine.assimilation.services."
            + path.stem
        )

        forbidden = set(orchestration_modules)

        forbidden.update(
            module
            for module in service_modules
            if module != current_module
        )

        assert_no_forbidden_imports(
            facts,
            forbidden,
        )

    print("[PASS] Services obey downward dependency direction")
    print("[PASS] Services remain isolated from sibling services")


def verify_handler_boundaries() -> None:
    """Handlers orchestrate object behavior but do not own SQL."""

    forbidden_sql = (
        "SELECT ",
        "INSERT INTO ",
        "UPDATE ",
        "DELETE FROM ",
        "CREATE TABLE ",
        "ALTER TABLE ",
    )

    forbidden_imports = (
        "knowledge_engine.storage.database",
        "sqlite3",
    )

    for path in python_files(HANDLERS_ROOT):
        if path.name == "__init__.py":
            continue

        facts = inspect_source(path)

        assert_no_sql_tokens(
            facts,
            forbidden_tokens=forbidden_sql,
        )

        assert_no_forbidden_imports(
            facts,
            forbidden_imports,
        )

    print("[PASS] Handlers contain no SQL")
    print("[PASS] Handlers avoid direct database implementations")


def verify_director_boundaries() -> None:
    """The Director must depend on abstractions, not concrete handlers."""

    facts = inspect_source(DIRECTOR_PATH)

    forbidden = (
        "knowledge_engine.assimilation.handlers.single_document",
        "knowledge_engine.assimilation.handlers.source_collection",
    )

    assert_no_forbidden_imports(
        facts,
        forbidden,
    )

    assert_contains_import(
        facts,
        "knowledge_engine.assimilation.registry_builder",
    )

    print("[PASS] Director avoids concrete handler imports")
    print("[PASS] Director resolves handlers through composition root")


def verify_registry_builder_composition_root() -> None:
    """
    Concrete handler construction belongs in registry_builder.py only.
    """

    builder = inspect_source(REGISTRY_BUILDER_PATH)

    assert_contains_import(
        builder,
        "knowledge_engine.assimilation.handlers.single_document",
    )

    assert_contains_import(
        builder,
        "knowledge_engine.assimilation.handlers.source_collection",
    )

    for path in (
        DIRECTOR_PATH,
        RUNNER_PATH,
    ):
        facts = inspect_source(path)

        assert_no_forbidden_imports(
            facts,
            (
                "knowledge_engine.assimilation.handlers.single_document",
                "knowledge_engine.assimilation.handlers.source_collection",
            ),
        )

    print("[PASS] Registry builder owns concrete handler composition")


def verify_runner_orchestration_boundary() -> None:
    """
    The Runner coordinates services but must not reclaim extracted
    responsibilities.
    """

    facts = inspect_source(RUNNER_PATH)

    required_services = (
        "knowledge_engine.assimilation.services.attempts",
        "knowledge_engine.assimilation.services.extraction",
        "knowledge_engine.assimilation.services.persistence",
        "knowledge_engine.assimilation.services.state",
    )

    for required in required_services:
        assert_contains_import(
            facts,
            required,
        )

    forbidden_imports = (
        "knowledge_engine.assimilation.single_document.read_text",
        "knowledge_engine.assimilation.single_document.chunk_text",
        "knowledge_engine.assimilation.single_document.checksum",
    )

    assert_no_forbidden_imports(
        facts,
        forbidden_imports,
    )

    forbidden_calls = {
        "read_text",
        "chunk_text",
        "checksum",
    }

    call_violations = sorted(
        call
        for call in facts.calls
        if call in forbidden_calls
        or call.rsplit(".", 1)[-1] in forbidden_calls
    )

    assert not call_violations, (
        f"{relative(RUNNER_PATH)} reintroduced extraction calls: "
        f"{call_violations}"
    )

    forbidden_sql = (
        "INSERT INTO DOCUMENT_TEXT",
        "DELETE FROM CHUNKS",
        "INSERT INTO CHUNKS",
        "INSERT INTO KNOWLEDGE_ASSIMILATION_ATTEMPTS",
        "UPDATE KNOWLEDGE_ASSIMILATION_ATTEMPTS",
    )

    assert_no_sql_tokens(
        facts,
        forbidden_tokens=forbidden_sql,
    )

    print("[PASS] Runner delegates to all four assimilation services")
    print("[PASS] Runner contains no direct extraction calls")
    print("[PASS] Runner contains no extracted-content SQL")
    print("[PASS] Runner contains no attempt-journal SQL")


def verify_repository_ownership() -> None:
    """Ensure Knowledge Registry SQL lives in its repository."""

    repository = inspect_source(
        KNOWLEDGE_REGISTRY_REPOSITORY_PATH
    )

    assert_has_sql_tokens(
        repository,
        required_tokens=(
            "SELECT",
            "FROM KNOWLEDGE_REGISTRY",
        ),
    )

    for path in python_files(HANDLERS_ROOT):
        if path.name == "__init__.py":
            continue

        facts = inspect_source(path)

        assert_no_sql_tokens(
            facts,
            forbidden_tokens=(
                "FROM KNOWLEDGE_REGISTRY",
                "UPDATE KNOWLEDGE_REGISTRY",
                "INSERT INTO KNOWLEDGE_REGISTRY",
                "DELETE FROM KNOWLEDGE_REGISTRY",
            ),
        )

    print("[PASS] KnowledgeRegistryRepository owns registry reads")
    print("[PASS] Handlers contain no Knowledge Registry SQL")


def verify_service_ownership() -> None:
    """Ensure extracted responsibilities live in their designated services."""

    extraction = inspect_source(
        EXTRACTION_SERVICE_PATH
    )
    persistence = inspect_source(
        PERSISTENCE_SERVICE_PATH
    )
    attempts = inspect_source(
        ATTEMPT_SERVICE_PATH
    )
    state = inspect_source(
        STATE_SERVICE_PATH
    )

    required_extraction_calls = {
        "read_text",
        "chunk_text",
        "checksum",
    }

    extraction_call_names = {
        call.rsplit(".", 1)[-1]
        for call in extraction.calls
    }

    missing_extraction_calls = sorted(
        required_extraction_calls
        - extraction_call_names
    )

    assert not missing_extraction_calls, (
        f"{relative(EXTRACTION_SERVICE_PATH)} is missing owned "
        f"extraction calls: {missing_extraction_calls}"
    )

    assert_has_sql_tokens(
        persistence,
        required_tokens=(
            "INSERT INTO DOCUMENT_TEXT",
            "DELETE FROM CHUNKS",
            "INSERT INTO CHUNKS",
        ),
    )

    assert_has_sql_tokens(
        attempts,
        required_tokens=(
            "INSERT INTO KNOWLEDGE_ASSIMILATION_ATTEMPTS",
            "UPDATE KNOWLEDGE_ASSIMILATION_ATTEMPTS",
        ),
    )

    assert_has_sql_tokens(
        state,
        required_tokens=(
            "UPDATE KNOWLEDGE_REGISTRY",
            "UPDATE KNOWLEDGE_ASSIMILATION_QUEUE",
        ),
    )

    print("[PASS] ExtractionService owns extraction and chunking")
    print("[PASS] PersistenceService owns document and chunk SQL")
    print("[PASS] AttemptJournalService owns attempt SQL")
    print("[PASS] StateService owns registry and queue transitions")


def main() -> None:
    verify_service_dependency_direction()
    verify_handler_boundaries()
    verify_director_boundaries()
    verify_registry_builder_composition_root()
    verify_runner_orchestration_boundary()
    verify_repository_ownership()
    verify_service_ownership()

    print("----------------------------------------------------------------------")
    print("[PASS] All assimilation architecture contracts verified")


if __name__ == "__main__":
    main()
