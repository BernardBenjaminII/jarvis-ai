"""Database-free append-only JSONL storage for VI-A6.8 Part A."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Iterator

from .repository_contracts import TimelineRepositoryStorageError


class AppendOnlyTimelineStorage:
    """Owns a single repository JSONL file and permits append/read only."""

    def __init__(self, root: str | Path, *, filename: str = "executive.timeline.jsonl") -> None:
        root_path = Path(root).expanduser().resolve()
        if not filename or Path(filename).name != filename:
            raise TimelineRepositoryStorageError("filename must be a plain file name.")
        self._root = root_path
        self._path = (root_path / filename).resolve()
        try:
            self._path.relative_to(root_path)
        except ValueError as exc:
            raise TimelineRepositoryStorageError("Storage path escaped repository root.") from exc
        self._root.mkdir(parents=True, exist_ok=True)
        if self._path.exists() and not self._path.is_file():
            raise TimelineRepositoryStorageError("Timeline storage path is not a regular file.")

    @property
    def root(self) -> Path:
        return self._root

    @property
    def path(self) -> Path:
        return self._path

    @property
    def size_bytes(self) -> int:
        return self._path.stat().st_size if self._path.exists() else 0

    def append(self, line: bytes) -> None:
        self.append_many((line,))

    def append_many(self, lines: Iterable[bytes]) -> None:
        material = tuple(lines)
        if not material:
            return
        for line in material:
            if not isinstance(line, bytes):
                raise TimelineRepositoryStorageError("Storage accepts bytes only.")
            if not line.endswith(b"\n") or line.count(b"\n") != 1:
                raise TimelineRepositoryStorageError("Each append must contain exactly one JSONL record.")
        try:
            with self._path.open("ab", buffering=0) as handle:
                for line in material:
                    handle.write(line)
                os.fsync(handle.fileno())
        except OSError as exc:
            raise TimelineRepositoryStorageError(f"Timeline append failed: {exc}") from exc

    def iter_lines(self) -> Iterator[bytes]:
        if not self._path.exists():
            return
        try:
            with self._path.open("rb") as handle:
                for number, line in enumerate(handle, 1):
                    if not line.endswith(b"\n"):
                        raise TimelineRepositoryStorageError(
                            f"Incomplete timeline record at line {number}."
                        )
                    yield line[:-1]
        except OSError as exc:
            raise TimelineRepositoryStorageError(f"Timeline read failed: {exc}") from exc
