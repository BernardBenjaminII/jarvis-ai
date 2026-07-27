from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping


class FileKind(str, Enum):
    PYTHON = "python"
    MARKDOWN = "markdown"
    SHELL = "shell"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    TEXT = "text"
    OTHER = "other"


class EvidenceClass(str, Enum):
    """Governance classification applied to discovered repository objects."""

    SOURCE = "source"
    GENERATED = "generated"
    EXTERNAL = "external"


class DiagnosticSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class PythonSymbolKind(str, Enum):
    CLASS = "class"
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    VARIABLE = "variable"


@dataclass(frozen=True, slots=True)
class ParseDiagnostic:
    path: str
    parser: str
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    exception_type: str | None = None
    line: int | None = None
    column: int | None = None


@dataclass(frozen=True, slots=True)
class RepositoryFile:
    repository_id: str
    path: str
    kind: FileKind
    size_bytes: int
    sha256: str
    evidence_class: EvidenceClass = EvidenceClass.SOURCE
    is_package_marker: bool = False
    is_test: bool = False
    is_verification: bool = False
    is_architecture_document: bool = False
    is_adr: bool = False
    is_constitutional_document: bool = False
    is_whitepaper: bool = False


@dataclass(frozen=True, slots=True)
class PythonImport:
    module: str
    names: tuple[str, ...] = ()
    level: int = 0
    line: int | None = None


@dataclass(frozen=True, slots=True)
class PythonSymbol:
    name: str
    qualified_name: str
    kind: PythonSymbolKind
    line: int
    end_line: int | None
    decorators: tuple[str, ...] = ()
    bases: tuple[str, ...] = ()
    is_public: bool = True
    is_dataclass: bool = False
    is_enum: bool = False
    is_protocol: bool = False
    is_exception: bool = False
    docstring: str | None = None


@dataclass(frozen=True, slots=True)
class PythonModule:
    repository_id: str
    path: str
    module_name: str
    package_name: str | None
    docstring: str | None
    imports: tuple[PythonImport, ...] = ()
    symbols: tuple[PythonSymbol, ...] = ()
    declared_all: tuple[str, ...] = ()
    inferred_public_exports: tuple[str, ...] = ()
    diagnostics: tuple[ParseDiagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class MarkdownHeading:
    level: int
    title: str
    line: int
    anchor: str


@dataclass(frozen=True, slots=True)
class MarkdownLink:
    label: str
    target: str
    line: int


@dataclass(frozen=True, slots=True)
class MarkdownDocument:
    repository_id: str
    path: str
    title: str | None
    document_id: str | None
    status: str | None
    headings: tuple[MarkdownHeading, ...] = ()
    links: tuple[MarkdownLink, ...] = ()
    adr_references: tuple[str, ...] = ()
    constitutional_references: tuple[str, ...] = ()
    architecture_references: tuple[str, ...] = ()
    diagnostics: tuple[ParseDiagnostic, ...] = ()


@dataclass(frozen=True, slots=True)
class RepositoryStatistics:
    total_files: int
    total_bytes: int
    python_files: int
    markdown_files: int
    shell_files: int
    package_markers: int
    test_files: int
    verification_files: int
    architecture_documents: int
    adr_documents: int
    constitutional_documents: int
    whitepapers: int
    python_modules: int
    python_symbols: int
    markdown_documents: int
    diagnostics: int
    source_files: int = 0
    generated_files: int = 0
    external_files: int = 0


@dataclass(frozen=True, slots=True)
class RepositoryInventory:
    schema_version: str
    root_name: str
    files: tuple[RepositoryFile, ...]
    python_modules: tuple[PythonModule, ...]
    markdown_documents: tuple[MarkdownDocument, ...]
    diagnostics: tuple[ParseDiagnostic, ...]
    statistics: RepositoryStatistics
    fingerprint: str


def to_primitive(value: Any) -> Any:
    """Convert immutable audit models into deterministic JSON primitives."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value):
        return {key: to_primitive(item) for key, item in asdict(value).items()}
    if isinstance(value, Mapping):
        return {str(key): to_primitive(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [to_primitive(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [to_primitive(item) for item in sorted(value, key=repr)]
    return value


def ordered_tuple(items: Iterable[Any], *, key: Any) -> tuple[Any, ...]:
    return tuple(sorted(items, key=key))
