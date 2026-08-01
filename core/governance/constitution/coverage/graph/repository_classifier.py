from __future__ import annotations
from pathlib import PurePosixPath
from .repository_contracts import RepositoryLifecycleState, RepositoryNodeKind

def normalize_path(value: str) -> str:
    return str(PurePosixPath(value.replace("\\", "/")))

def classify_repository_path(path: str) -> RepositoryNodeKind:
    normalized = normalize_path(path)
    p = PurePosixPath(normalized)
    name, suffix = p.name.lower(), p.suffix.lower()
    parts = tuple(part.lower() for part in p.parts)
    if normalized in {".", "", "/"}:
        return RepositoryNodeKind.REPOSITORY
    if name in {"pyproject.toml", "setup.cfg", "setup.py", "tox.ini", ".env"}:
        return RepositoryNodeKind.CONFIGURATION
    if suffix in {".yaml", ".yml", ".toml", ".ini", ".cfg", ".json"}:
        return RepositoryNodeKind.CONFIGURATION
    if "tests" in parts or name.startswith("test_") or name.endswith("_test.py"):
        return RepositoryNodeKind.TEST
    if "verification" in parts or name.startswith("verify_"):
        return RepositoryNodeKind.VERIFICATION
    if suffix in {".md", ".rst", ".txt", ".adoc"} or "docs" in parts:
        return RepositoryNodeKind.DOCUMENT
    if suffix in {".sh", ".bash", ".zsh"} or (suffix == "" and ("bin" in parts or "scripts" in parts)):
        return RepositoryNodeKind.EXECUTABLE
    if suffix in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java"}:
        return RepositoryNodeKind.MODULE
    if suffix in {".sqlite", ".db", ".csv", ".parquet", ".jsonl"}:
        return RepositoryNodeKind.DATA_ARTIFACT
    if suffix == "" and name:
        return RepositoryNodeKind.PACKAGE
    return RepositoryNodeKind.UNKNOWN

def infer_lifecycle_state(node_kind: RepositoryNodeKind, attributes: dict[str, object]) -> RepositoryLifecycleState:
    explicit = str(attributes.get("lifecycle_state", "")).strip().lower()
    for state in RepositoryLifecycleState:
        if explicit == state.value:
            return state
    if bool(attributes.get("certified", False)):
        return RepositoryLifecycleState.CERTIFIED
    mapping = {
        RepositoryNodeKind.TEST: RepositoryLifecycleState.TESTED,
        RepositoryNodeKind.VERIFICATION: RepositoryLifecycleState.CERTIFIED,
        RepositoryNodeKind.DOCUMENT: RepositoryLifecycleState.DOCUMENTED,
        RepositoryNodeKind.CONFIGURATION: RepositoryLifecycleState.CONFIGURED,
        RepositoryNodeKind.UNKNOWN: RepositoryLifecycleState.UNKNOWN,
    }
    return mapping.get(node_kind, RepositoryLifecycleState.IMPLEMENTED)
