"""Database-free append-only JSONL storage for the Executive Timeline."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
from typing import Iterable, Iterator

from .locking import TimelineInterprocessLock
from .repository_contracts import TimelineRepositoryStorageError


class AppendOnlyTimelineStorage:
    """Own one JSONL authority plus its interprocess lock."""

    def __init__(
        self,
        root: str | Path,
        *,
        filename: str = "executive.timeline.jsonl",
        lock_filename: str = "executive.timeline.lock",
    ) -> None:
        root_path = Path(root).expanduser().resolve()

        for candidate, label in (
            (filename, "filename"),
            (lock_filename, "lock_filename"),
        ):
            if not candidate or Path(candidate).name != candidate:
                raise TimelineRepositoryStorageError(
                    f"{label} must be a plain file name."
                )

        self._root = root_path
        self._path = (root_path / filename).resolve()
        self._lock_path = (root_path / lock_filename).resolve()

        for path in (self._path, self._lock_path):
            try:
                path.relative_to(root_path)
            except ValueError as exc:
                raise TimelineRepositoryStorageError(
                    "Storage path escaped repository root."
                ) from exc

        self._root.mkdir(parents=True, exist_ok=True)

        if self._path.exists() and not self._path.is_file():
            raise TimelineRepositoryStorageError(
                "Timeline storage path is not a regular file."
            )

        self._lock = TimelineInterprocessLock(self._lock_path)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def path(self) -> Path:
        return self._path

    @property
    def lock_path(self) -> Path:
        return self._lock_path

    @property
    def size_bytes(self) -> int:
        return self._path.stat().st_size if self._path.exists() else 0

    @contextmanager
    def exclusive(self) -> Iterator[None]:
        with self._lock.acquire():
            yield

    def append(self, line: bytes) -> None:
        self.append_many((line,))

    def append_many(self, lines: Iterable[bytes]) -> None:
        """Lock and append when storage is used directly."""
        with self.exclusive():
            self.append_many_unlocked(lines)

    def append_many_unlocked(self, lines: Iterable[bytes]) -> None:
        """Append while the caller already owns the repository lock."""
        material = tuple(lines)
        if not material:
            return

        for line in material:
            if not isinstance(line, bytes):
                raise TimelineRepositoryStorageError(
                    "Storage accepts bytes only."
                )
            if not line.endswith(b"\n") or line.count(b"\n") != 1:
                raise TimelineRepositoryStorageError(
                    "Each append must contain exactly one JSONL record."
                )

        try:
            with self._path.open("ab", buffering=0) as handle:
                for line in material:
                    handle.write(line)
                os.fsync(handle.fileno())
        except OSError as exc:
            raise TimelineRepositoryStorageError(
                f"Timeline append failed: {exc}"
            ) from exc

    def iter_lines(self) -> Iterator[bytes]:
        if not self._path.exists():
            return

        try:
            with self._path.open("rb") as handle:
                for number, line in enumerate(handle, 1):
                    if not line.endswith(b"\n"):
                        raise TimelineRepositoryStorageError(
                            "Incomplete timeline record at "
                            f"line {number}."
                        )
                    yield line[:-1]
        except OSError as exc:
            raise TimelineRepositoryStorageError(
                f"Timeline read failed: {exc}"
            ) from exc
