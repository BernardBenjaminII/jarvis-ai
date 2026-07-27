from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .models import EvidenceClass, FileKind, RepositoryFile


_DEFAULT_IGNORES = frozenset({
    ".git", ".hg", ".svn", ".idea", ".vscode", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", "__pycache__", "node_modules", ".venv", "venv", "dist", "build",
    ".migration_backups", "coverage", "htmlcov",
    # Generated operational outputs are not repository source evidence and must not
    # recursively influence the inventory that produces them.
    "artifacts", "reports", "logs",
})

_GENERATED_ROOTS = frozenset({"artifacts", "coverage", "htmlcov", "reports", "logs", "dist", "build"})
_EXTERNAL_ROOTS = frozenset({"downloads", "external", "vendor", "third_party"})


@dataclass(frozen=True, slots=True)
class ScanPolicy:
    ignored_directory_names: frozenset[str] = _DEFAULT_IGNORES
    ignored_file_names: frozenset[str] = frozenset({".DS_Store"})
    include_hidden_files: bool = False


class DeterministicFilesystemScanner:
    def __init__(self, policy: ScanPolicy | None = None) -> None:
        self._policy = policy or ScanPolicy()

    def scan(self, root: Path) -> tuple[RepositoryFile, ...]:
        root = root.expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError(f"Repository root does not exist or is not a directory: {root}")

        files: list[RepositoryFile] = []
        for path in self._walk(root):
            relative = path.relative_to(root).as_posix()
            kind = classify_file(path)
            digest = sha256_file(path)
            files.append(
                RepositoryFile(
                    repository_id=stable_repository_id(relative, digest),
                    path=relative,
                    kind=kind,
                    size_bytes=path.stat().st_size,
                    sha256=digest,
                    evidence_class=classify_evidence(relative),
                    is_package_marker=path.name == "__init__.py",
                    is_test=_is_test(relative),
                    is_verification=_is_verification(relative),
                    is_architecture_document=_is_architecture_document(relative),
                    is_adr=_is_adr(relative),
                    is_constitutional_document=_is_constitutional(relative),
                    is_whitepaper=_is_whitepaper(relative),
                )
            )
        return tuple(sorted(files, key=lambda item: item.path))

    def _walk(self, root: Path) -> Iterable[Path]:
        stack = [root]
        while stack:
            current = stack.pop()
            entries = sorted(current.iterdir(), key=lambda p: p.name.casefold(), reverse=True)
            for entry in entries:
                if entry.is_dir():
                    if self._skip_directory(entry):
                        continue
                    stack.append(entry)
                elif entry.is_file() and not self._skip_file(entry):
                    yield entry

    def _skip_directory(self, path: Path) -> bool:
        if path.name in self._policy.ignored_directory_names:
            return True
        return path.name.startswith(".") and not self._policy.include_hidden_files

    def _skip_file(self, path: Path) -> bool:
        if path.name in self._policy.ignored_file_names:
            return True
        return path.name.startswith(".") and not self._policy.include_hidden_files


def classify_evidence(relative_path: str) -> EvidenceClass:
    first = relative_path.replace("\\", "/").split("/", 1)[0].casefold()
    if first in _GENERATED_ROOTS:
        return EvidenceClass.GENERATED
    if first in _EXTERNAL_ROOTS:
        return EvidenceClass.EXTERNAL
    return EvidenceClass.SOURCE


def classify_file(path: Path) -> FileKind:
    suffix = path.suffix.lower()
    return {
        ".py": FileKind.PYTHON, ".md": FileKind.MARKDOWN, ".markdown": FileKind.MARKDOWN,
        ".sh": FileKind.SHELL, ".bash": FileKind.SHELL, ".json": FileKind.JSON,
        ".yaml": FileKind.YAML, ".yml": FileKind.YAML, ".toml": FileKind.TOML,
        ".txt": FileKind.TEXT,
    }.get(suffix, FileKind.OTHER)


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def stable_repository_id(relative_path: str, sha256: str) -> str:
    seed = f"{relative_path}\0{sha256}".encode("utf-8")
    return f"REP-{hashlib.sha256(seed).hexdigest()[:16].upper()}"


def _is_test(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return "tests" in parts or name.startswith("test_") or name.endswith("_test.py")


def _is_verification(path: str) -> bool:
    lowered = path.lower()
    return "/verification/" in f"/{lowered}" or lowered.startswith("dev/verify_") or "/verify_" in lowered


def _is_architecture_document(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("docs/architecture/") or "/architecture/" in lowered


def _is_adr(path: str) -> bool:
    return Path(path).name.upper().startswith("ADR-")


def _is_constitutional(path: str) -> bool:
    lowered = path.lower()
    name = Path(path).name.lower()
    return lowered.startswith("docs/constitution/") or "constitution" in name or name.startswith(("con-", "const-", "km-"))


def _is_whitepaper(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith("docs/whitepapers/") or Path(path).name.upper().startswith("WP-")
