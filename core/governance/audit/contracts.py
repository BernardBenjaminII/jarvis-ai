from __future__ import annotations

from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable

from .models import MarkdownDocument, PythonModule, RepositoryFile, RepositoryInventory


@runtime_checkable
class FilesystemScanner(Protocol):
    def scan(self, root: Path) -> tuple[RepositoryFile, ...]: ...


@runtime_checkable
class PythonSourceParser(Protocol):
    def parse(self, root: Path, file: RepositoryFile) -> PythonModule: ...


@runtime_checkable
class MarkdownSourceParser(Protocol):
    def parse(self, root: Path, file: RepositoryFile) -> MarkdownDocument: ...


@runtime_checkable
class InventoryBuilder(Protocol):
    def build(self, root: Path, output_directory: Path | None = None) -> RepositoryInventory: ...
